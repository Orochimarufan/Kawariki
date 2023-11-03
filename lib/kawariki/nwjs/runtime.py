import json
import os
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from shutil import copytree
from tempfile import NamedTemporaryFile
from typing import IO, ContextManager, Dict, List, Literal, Optional, Sequence, Tuple, Union

from ..app import App, IRuntime
from ..distribution import Distribution, DistributionInfo
from ..game import Game
from ..misc import ErrorCode, copy_unlink, version_str
from ..process import ProcessLaunchInfo
from .package import PackageNw


class NWjsDistributionInfo(DistributionInfo):
    sdk: bool


class GreenworksDistInfo(DistributionInfo):
    nwjs: Sequence[Sequence[int]]   # Required


class NWjs(Distribution):
    """ A distribution of NW.js """
    info: NWjsDistributionInfo

    @property
    def is_sdk(self) -> bool:
        """ Whether distribution includes SDK features """
        return self.info.get("sdk", False)

    @classmethod
    def load_variants(cls, info: NWjsDistributionInfo, dist_path: Path, platform=None,
                      platform_map: Optional[Dict[str, str]] = None,
                      defaults: Optional[NWjsDistributionInfo] = None):
        """ Synthesize sdk and non-sdk variants if sdk=synthesize """
        if info.get('sdk', defaults.get('sdk', None) if defaults else None) == "synthesize":
            alias: Sequence[str] = info.get('alias', [])
            info_sdk = info.copy()
            info_sdk.update(sdk=True, alias=[*alias, *(f"{a}-sdk" for a in alias)])
            info_nosdk = info.copy()
            info_nosdk.update(sdk=False, alias=[*alias, *(f"{a}-nosdk" for a in alias)])
            infos = (info_nosdk, info_sdk)
        else:
            infos = (info,)
        return (cls(info, dist_path, platform, platform_map, defaults) for info in infos)


class GreenworksDistribution(Distribution):
    """ A distribution of Greenworks for NW.js """
    info: GreenworksDistInfo

    @property
    def nwjs_version(self) -> Tuple[int, ...]:
        """ The first compatible NW.js version """
        return tuple(self.info["nwjs"][0])

    def is_compatible(self, nwjs: NWjs) -> bool:
        """ Check whether this Greenworks distribution works with a specific NW.js version """
        return any(nwjs.version[:len(ver)] == tuple(ver) for ver in self.info["nwjs"])


def overlay_or_clobber(pkg: PackageNw, proc: ProcessLaunchInfo,
                       filename: str, mode: Literal["a", "w"]="w") -> ContextManager[IO[str]]:
    """ Clobber file if pkg.may_clobber, otherwise use proc.replace_file  to overlay """
    path = pkg.path / filename
    if pkg.may_clobber:
        return path.open(mode)
    return proc.replace_file(path, mode)


class Runtime(IRuntime):
    """ Kawariki runtime for NW.js based games """
    app: App
    base: Path
    overlayns_bin: Path
    nwjs_dist_path: Path
    greenworks_dist_path: Path

    def __init__(self, app: App):
        self.app = app
        self.base_path = app.app_root / "nwjs"
        self.overlayns_bin = app.app_root / "overlayns-static"
        self.nwjs_dist_path = app.dist_path / "nwjs"
        self.greenworks_dist_path = app.dist_path / "nwjs-greenworks"

    # +-------------------------------------------------+
    # NW.js versions
    # +-------------------------------------------------+
    @cached_property
    def nwjs_versions(self) -> Sequence[NWjs]:
        """ All compatible distributions of NW.js from versions.json """
        return NWjs.load_json(self.base_path / "versions.json", self.nwjs_dist_path, self.app.platform)

    def get_nwjs(self, version_name: str) -> Optional[NWjs]:
        """ Get a specific NW.js distribution by alias """
        for ver in self.nwjs_versions:
            if ver.match(version_name):
                return ver
        return None

    def get_nwjs_version(self,
                         minver: Optional[Tuple[int, ...]]=None,
                         maxver: Optional[Tuple[int, ...]]=None,
                         sdk: Optional[bool]=None) -> Optional[NWjs]:
        """
        Get the latest NW.js version available matching the requirements

        :param min: Minimum version (inclusive)
        :param max: Maximum version (inclusive)
        :param sdk: Require DevTools-enabled distribution
        """
        if v := sorted([ver for ver in self.nwjs_versions
                        if all(((minver is None or minver <= ver.version),
                                (maxver is None or maxver >= ver.version),
                                (not sdk or ver.is_sdk)))],
                       key=lambda ver: (ver.version, ver.available, not ver.is_sdk)):
            return v[-1]
        return None

    def select_nwjs_version(self, game: Game, nwjs_name: Optional[str]=None, sdk: Optional[bool]=False) -> NWjs:
        """
        Select NW.js distribution suitable for game

        :param game: The game
        :param nwjs_name: A specific NW.js distribution name that was configured
        :param sdk: Whether to return a SDK distribution. Ignored if nwjs_name is given.
        :raise ErrorCode:
        """
        nwjs = None

        if nwjs_name is not None:
            nwjs = self.get_nwjs(nwjs_name)
            if nwjs is None:
                self.app.show_error(f"Specified NW.js version '{nwjs_name}' doesn't exist. Check nwjs/versions.json")
                raise ErrorCode(5)
            print(f"Using specified NW.js version '{nwjs_name}' ({nwjs.name})")

        if game.is_rpgmaker:
            print(f"Looks like RPGMaker {game.rpgmaker_release} {version_str(game.rpgmaker_version or ())}")

            if game.is_rpgmaker_mv_legacy:
                if game.rpgmaker_version is None:
                    self.app.show_warn("Missing RPGMaker MV version in rpg_core.js. Assuming old version.")
                if os.environ.get("KAWARIKI_NWJS_IGNORE_LEGACY_MV", None):
                    print("Using modern Nw.js with legacy RPGMaker MV version (KAWARIKI_NWJS_IGNORE_LEGACY_MV=1)")
                elif nwjs is not None:
                    if nwjs.version >= (0, 13):
                        self.app.show_warn(
                            "Overriding NW.js version for legacy RMMV (before 1.6) game.\n"
                            f"Selected version is {nwjs.version}, "
                            "but legacy RMMV may not work correctly with NW.js > 0.12.x")
                else:
                    print("Trying to use NW.js suitable for legacy RMMV (before 1.6)")
                    nwjs = self.get_nwjs_version(maxver=(0, 12, 99))
                    if nwjs is None:
                        self.app.show_warn(
                            "No NW.js version suitable for RMMV before 1.6 found (requires NW.js older than 0.13)\n"
                            "Now trying to run the game with modern NW.js, but YMMV")
        elif game.tyrano_version:
            print(f"Looks like Tyrano builder v{game.tyrano_version}")

        if nwjs is None:
            nwjs = self.get_nwjs_version(minver=(0, 13), sdk=sdk)
            if nwjs is None:
                self.app.show_error("No suitable NW.js version found in nwjs/versions.json")
                raise ErrorCode(6)
            print(f"Selected NW.js version: {nwjs.name}")

        return nwjs

    # Download
    def try_download_nwjs(self, nwjs: NWjs):
        """
        Download nwjs distribution

        :param nwjs: The version to download
        :raise ErrorCode: on error
        """
        from ..download import download_dist_progress_archive

        try:
            download_dist_progress_archive(self.app, nwjs)
        except Exception as e:
            import traceback
            self.app.show_error(f"Couldn't download {nwjs.name}:\n{traceback.format_exc()}")
            raise ErrorCode(10) from e

        self.app.show_info(f"Finished downloading NW.js distribution '{nwjs.name}'")

    def select_and_download_nwjs(self, game: Game, nwjs_name: Optional[str]=None, sdk: Optional[bool]=False) -> NWjs:
        """ Select and then (if needed) download an appropriate NW.js distribution """
        # Select nwjs version
        nwjs = self.select_nwjs_version(game, nwjs_name, sdk)

        # Download NW.js version
        if not nwjs.available:
            self.try_download_nwjs(nwjs)

        if not os.access(nwjs.binary, os.X_OK | os.F_OK):
            self.app.show_error(f"Entry '{nwjs.name}' in nwjs/versions.json is broken:\n'{nwjs.binary}' doesn't exist")
            raise ErrorCode(6)

        return nwjs

    @cached_property
    def greenworks_versions(self) -> Sequence[GreenworksDistribution]:
        """ All Greenworks distributions for the current platform """
        return GreenworksDistribution.load_json(self.base_path / "greenworks.json",
                                                self.greenworks_dist_path,
                                                self.app.platform)

    def get_greenworks(self, nwjs: NWjs) -> Optional[GreenworksDistribution]:
        """ Select a Greenworks distribution compatible with a NW.js distribution """
        for gw in self.greenworks_versions:
            if gw.is_compatible(nwjs):
                return gw
        return None

    # +-------------------------------------------------+
    #   Run NW.js for Game
    # +-------------------------------------------------+
    def _inject_file(self,
                     pkg: PackageNw,
                     proc: ProcessLaunchInfo,
                     mode: Union[Literal["preload"], Literal["inject"]],
                     scripts: Sequence[Path],
                     code: Optional[Sequence[str]]=None):
        """ Create a file to be set as bg_script/inject """
        with NamedTemporaryFile("w", dir=pkg.path, prefix=f"{mode}-", suffix=".js", delete=False) as f:
        #with proc.temp_file(prefix=f"{mode}-", suffix=".js") as f:
            name = os.path.basename(f.name)
            f.write(f"// Kawariki NW.js {mode} script\n")
            f.write(f"console.log('[Kawariki] Injected {os.path.basename(f.name)}');\n")
            if mode == "preload":
                for script in scripts:
                    f.write(f"require('{script}');\n")
            elif mode == "inject":
                f.write("""(function() {
                    var head = document.head ? document.head : document.documentElement;
                    function addScript(path) {
                        var el = document.createElement("script");
                        el.type = "text/javascript";
                        el.src = path;
                        head.appendChild(el);
                    }
                    """)
                for script in scripts:
                    escaped = str(script).replace('"', r'\\"')
                    f.write(f"addScript(\"file://{escaped}\");\n")
                f.write("})();\n")
            else:
                os.unlink(f.name)
                raise ValueError("Unknown _inject_file mode")
            if code:
                xcode = ";\n  ".join(code)
                f.write(f"(function() {{\n  {xcode};\n}})();\n")
            proc.at_cleanup(lambda: os.unlink(f.name))
            return name

    def overlay_greenworks(self, pkg: PackageNw, nwjs: NWjs, proc: ProcessLaunchInfo):
        """ Overlay appropriate Greenworks binaries over package """
        for path in pkg.path.rglob("greenworks.js"):
            greenworks = self.get_greenworks(nwjs)
            if not greenworks:
                self.app.show_warn(f"No Greenworks available for NW.js version {nwjs.version_str} ({nwjs.name})")
                break
            if not greenworks.available:
                from ..download import download_dist_progress_tar
                download_dist_progress_tar(self.app, greenworks)
            print(f"Patching Greenworks at '{path}'")
            ppath = path.parent
            # Just clobber files if we extracted package to temp
            if pkg.may_clobber:
                copytree(greenworks.path, ppath, dirs_exist_ok=True)
                continue
            # Unfortunately, overlayfs is currently incompatible with casefolding-enabled ext4.
            # Steam libraries are very likely to be on such a filesystem though.
            #overlayns.append("-o")
            #overlayns.append("{},shadow,lowerdir={},nodev,nosuid".format(ppath,r.nwjs_greenworks_path))
            # Instead, fall back to copies and bind mounts
            tempdir = proc.temp_dir(prefix=str(ppath.relative_to(pkg.path)).replace("/", "_"))
            if ',' in str(ppath) or ',' in str(tempdir):
                self.app.show_error("Comma in paths is currently not supported by overlayns\n"
                                    "Greenworks support disabled")
                continue
            copytree(ppath, tempdir, dirs_exist_ok=True)
            copytree(greenworks.path, tempdir, dirs_exist_ok=True, copy_function=copy_unlink)
            proc.overlayns_bind(tempdir, ppath)

    def overlay_files(self, game: Game, pkg: PackageNw, nwjs: NWjs, proc: ProcessLaunchInfo):
        if pkg.is_archive:
            raise RuntimeError("Cannot modify archived package directly")

        # Patch native greenworks (Steamworks API)
        if proc.have_overlayns:
            self.overlay_greenworks(pkg, nwjs, proc)
        else:
            print("Warning: overlayns not supported or explicitly disabled. Greenworks integration disabled.")

        # TODO: make configurable
        bg_scripts: List[Path] = []
        inject_scripts: List[Path] = []
        code: List[str] = []
        conf = pkg.read_json()

        # Try to use modern JS: ES2022/ES13 supported since Chromium 94/NW.js 0.57
        js = self.base_path / 'js'
        es_version = "es5" if nwjs.version < (0, 57) else "es13"
        ts = js / es_version

        def inject_script(path: Path, *, target=inject_scripts):
            if path.exists():
                target.append(path)
            else:
                print(f"Note: Script '{path.name}' isn't available with NW.js version {nwjs.version_str}")

        inject_script(js / "case-insensitive-nw.js", target=bg_scripts)

        if game.rpgmaker_release in ("MV", "MZ"):
            # Disable this if we can detect a rmmv  plugin that provides remapping?
            inject_script(ts / "rpg-remap.js")
            inject_script(ts / "rpg-vars.js")
            if os.environ.get("KAWARIKI_NWJS_RPG_DECRYPTED_ASSETS"):
                if game.is_rpgmaker_mv_legacy or game.rpgmaker_release not in ("MV", "MZ"):
                    self.app.show_warn("RPGMaker version isn't supported for KAWARIKI_NWJS_RPG_DECRYPTED_ASSETS")
                else:
                    inject_script(js / f"{game.rpgmaker_release.lower()}-decrypted-assets.js")

        # User scripts
        for userscript in pkg.enclosing_directory.glob("*.kawariki.js"):
            print(f"Found UserScript {userscript}")
            inject_scripts.append(userscript.absolute())

        # Patch Tyrano builder https://github.com/ShikemokuMK/tyranoscript/issues/87
        if game.tyrano_version is not None:
            print("Patching tyrano builder to assume PC")
            with overlay_or_clobber(pkg, proc, "tyrano/libs.js", "a") as f:
                f.write("""\n\n// Kawariki Patch\njQuery.userenv =  function(){return "pc";};\n""")

        if conf["main"].startswith("app://"):
            conf["main"] = conf["main"][6:]
            print("Fixed old package.json/main syntax")
        if "name" not in conf or not conf["name"]:
            conf["name"] = "Kawariki NW.js App"
            if conf["main"].endswith(".html"):
                with suppress(Exception): # Just keep default if anything fails
                    with open(pkg.path / conf["main"]) as f:
                        html = f.read()
                    start = html.find("<title>")
                    if start >= 0:
                        start += 7
                        end = html.find("</title>", start)
                        if end >= 0:
                            conf["name"] = html[start:end]

        if os.environ.get("KAWARIKI_NWJS_DEVTOOLS"):
            code.append("""(typeof nw !== "undefined"? nw : require("nw.gui")).Window.get().showDevTools()""")

        if os.environ.get("KAWARIKI_NWJS_INJECT_BG"):
            inject_scripts = [*bg_scripts, *inject_scripts]
            bg_scripts = []

        # Patch package json
        if nwjs.version >= (0, 19):
            if bg_scripts:
                conf['bg-script'] = self._inject_file(pkg, proc, "preload", bg_scripts)
            if inject_scripts or code:
                conf['inject_js_start'] = self._inject_file(pkg, proc, "inject", inject_scripts, code=code)
        else:
            if bg_scripts or inject_scripts or code:
                #modify main.html
                with open(pkg.path / conf["main"]) as f:
                    html = f.read()
                fn = self._inject_file(pkg, proc, "inject", bg_scripts + inject_scripts, code=code)
                html = html.replace("<head>", f"""<head><script src="file://{os.path.realpath(fn)}"></script>""")
                with overlay_or_clobber(pkg, proc, conf["main"]) as f:
                    f.write(html)

        with overlay_or_clobber(pkg, proc, pkg.json) as f:
            json.dump(conf, f)

    def run(self, game, arguments: Sequence[str],
            nwjs_name: Optional[str]=None, dry=False, sdk: Optional[bool]=None,
            no_overlayns=False, no_unpack=False) -> int:
        if not game.is_nwjs_app:
            raise RuntimeError("Called nwjs.Runtime.run with non-NW.js game")

        # Get suitable NW.js distro
        try:
            nwjs = self.select_and_download_nwjs(game, nwjs_name, sdk)
        except ErrorCode as e:
            return e.code

        pkg = game.package_nw
        proc = ProcessLaunchInfo(self.app, [nwjs.binary], no_overlayns=no_overlayns)

        # === Maybe unpack archive ===
        if pkg.is_archive:
            if no_unpack:
                self.app.show_warn("Running archived NW.js apps without unpacking is not fully supported.")
                no_overlayns = True
            else:
                tmp = proc.temp_dir(prefix="package-", suffix=".nw")
                print("Unpacking app to: ", tmp)
                pkg = pkg.unarchive(tmp, as_temp=True)

        path = pkg.path.relative_to(game.root) if pkg.path.is_relative_to(game.root) else pkg.path.resolve()
        proc.argv.extend([path, *arguments])
        proc.workingdir = game.root

        # === Patch some game files ===
        self.overlay_files(game, pkg, nwjs, proc)

        # === Execute ===
        print(f"Running {proc.argv_join()} in {game.root}")

        # FIXME: differentiate between overlayns and game/nwjs failure
        #        and offer to re-try without overlayns/greenworks support
        if not dry:
            proc.exec()
        proc.cleanup()

        return 0

    def get_patcher(self, game: Game):
        from .patcher import Patcher
        nwjs = self.select_and_download_nwjs(game)
        return Patcher(nwjs)
