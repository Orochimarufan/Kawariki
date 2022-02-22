import json
import os
import shlex
import subprocess
import tempfile
from functools import cached_property
from pathlib import Path
from shutil import copytree, copyfileobj
from typing import Optional, Sequence, Union

from ..app import App, IRuntime
from ..game import Game
from ..misc import ErrorCode, copy_unlink, version_str
from ..process import ProcessLaunchInfo


class NWjs:
    def __init__(self, info, path):
        self._path = path
        self.info = info

    @property
    def version(self):
        return tuple(self.info["version"])

    @property
    def name(self):
        return self.info.get("name", self.dist)

    @property
    def dist(self):
        return self.info["dist"]

    def get_path(self, component) -> Path:
        return self._path / component / self.info[component]

    def has(self, component):
        return bool(self.info.get(component, None))

    @property
    def binary(self):
        return self.get_path("dist") / "nw"

    @property
    def available(self):
        return self.get_path("dist").exists()

    def __repr__(self):
        return f"<Runtime.NWjs {version_str(self.version)} '{self.dist}' at 0x{id(self):x}>"


class Runtime(IRuntime):
    app: App
    base: Path
    overlayns_bin: Path

    def __init__(self, app: App):
        self.app = app
        self.base = app.app_root / "nwjs"
        self.overlayns_bin = app.app_root / "overlayns-static"

    # +-------------------------------------------------+
    # NW.js versions
    # +-------------------------------------------------+
    @cached_property
    def nwjs_versions(self):
        with open(self.base / "versions.json") as f:
            return [NWjs(i, self.base) for i in json.load(f)]

    def get_nwjs(self, version_name: str) -> Optional[NWjs]:
        for ver in self.nwjs_versions:
            if ver.name == version_name:
                return ver
        return None

    def get_nwjs_version(self, min=None, max=None, sdk=None) -> Optional[NWjs]:
        """
        Get the latest NW.js version available matching the requirements

        :param min: Minimum version (inclusive)
        :param max: Maximum version (inclusive)
        :param sdk: Require DevTools-enabled distribution
        """
        if v := sorted([ver for ver in self.nwjs_versions
                            if  (min is None or min <= ver.version)
                            and (max is None or max >= ver.version)
                            and (not sdk or ver.has("sdk"))],
                        key=lambda ver: (ver.version, ver.available, not ver.has("sdk"))):
            return v[-1]
        return None

    def select_nwjs_version(self, game: Game, nwjs_name: str=None, sdk=False) -> NWjs:
        """
        Select NW.js distribution suitable for game

        :param game: The game
        :param nwjs_name: A specific NW.js distribution name that was configured
        :param sdk: Whether to return a SDK distribution. Ignored if nwjs_name is given.
        :raise ErrorCode:
        """
        nwjs = None
        if nwjs_name is not None:
            if (nwjs := self.get_nwjs(nwjs_name)) is None:
                self.app.show_error(f"Specified NW.js version '{nwjs_name}' doesn't exist. Check nwjs-versions.json")
                raise ErrorCode(5)
            else:
                print(f"Using specified NW.js version '{nwjs_name}' ({nwjs.dist})")

        if game.is_rpgmaker:
            print(f"Looks like RPGMaker {game.rpgmaker_release} {version_str(game.rpgmaker_version or ())}")

            if game.is_rpgmaker_mv_legacy:
                if nwjs is not None:
                    if nwjs.version >= (0, 13):
                        self.app.show_warn(f"Overriding NW.js version for legacy RMMV (before 1.6) game.\nSelected version is {nwjs.version}, but legacy RMMV may only work correctly with NW.js up to 0.12.x")
                else:
                    print("Using NW.js suitable for legacy RMMV (before 1.6)")
                    nwjs = self.get_nwjs_version(max=(0, 12, 99))
                    if nwjs is None:
                        self.app.show_error("No NW.js version suitable for RMMV before 1.6 found (requires NW.js older than 0.13)\nYou can force an incompatible version using --nwjs, but YMMV")
                        raise ErrorCode(5)

        if nwjs is None:
            if (nwjs := self.get_nwjs_version(min=(0, 13), sdk=sdk)) is None:
                self.app.show_error("No suitable NW.js version found in nwjs-versions.json")
                raise ErrorCode(6)
            else:
                print(f"Selected NW.js version: {nwjs.dist}")
        
        return nwjs
    
    # Download
    def try_download_nwjs(self, nwjs: NWjs):
        """
        Download nwjs distribution

        :param nwjs: The version to download
        :raise ErrorCode: on error
        """
        from ..download import download_progress_tar

        if not nwjs.has("dist_url"):
            self.app.show_error(f"Cannot download NW.js distribution '{nwjs.dist}'\nnwjs-versions.json doesn't specify a download url.")
            raise ErrorCode(8)

        def strip_prefix(entry):
            # Figure out filename, strip prefix
            # there isn't really a good way of figuring out a common prefix in stream mode
            # so just strip the leading path component if it starts with nwjs- for now
            if '/' in entry.name:
                dir, name = entry.name.split("/", 1)
                if dir.startswith("nwjs-"):
                    entry.name = name

        try:
            download_progress_tar(self.app, nwjs.info["dist_url"], nwjs.get_path("dist"),
                description=f"Downloading NW.js distribution '{nwjs.dist}'",
                modify_entry=strip_prefix)
        except Exception:
            raise ErrorCode(10)

        self.app.show_info(f"Finished downloading NW.js distribution '{nwjs.dist}'")
    
    def select_and_download_nwjs(self, game: Game, nwjs_name: str=None, sdk=False) -> NWjs:
        # Select nwjs version
        nwjs = self.select_nwjs_version(game, nwjs_name, sdk)

        # Download NW.js version
        if not nwjs.available:
            self.try_download_nwjs(nwjs)

        if not os.access(nwjs.binary, os.X_OK|os.F_OK):
            self.app.show_error(f"Entry '{nwjs.name}' in nwjs-versions.json is broken:\n'{nwjs.binary}' doesn't exist")
            raise ErrorCode(6)
        
        return nwjs


    # +-------------------------------------------------+
    #   Run NW.js for Game
    # +-------------------------------------------------+
    def _inject_file(self, game, proc, mode, scripts):
        with tempfile.NamedTemporaryFile("w", dir=game.package_dir, prefix=f"{mode}-", suffix=".js", delete=False) as f:
            name = os.path.basename(f.name)
            f.write(f"// Kawariki NW.js {mode} script\n")
            f.write(f"console.log('[Kawariki] Injected {name}');\n")
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
                    f.write(f"addScript('file://{script}');\n")
                f.write("})();")
            else:
                os.unlink(f.name)
                raise ValueError("Unknown _inject_file mode")
            proc.at_cleanup(lambda: os.unlink(f.name))
            return name

    def overlay_files(self, game, nwjs, proc):
        # Use some namespace magic to leave the game install clean
        # This requires unprivileged user namespaces to be enabled in the kernel
        # In some versions of Ubuntu/Debian it can be enabled with 'sysctl -w kernel.unprivileged_userns_clone=1'

        # Patch native greenworks (Steamworks API)
        for path in game.root.rglob("greenworks.js"):
            if not nwjs.has("greenworks"):
                self.app.show_warn(f"Greenworks not available on NW.js version '{nwjs.name}' ({nwjs.dist})")
                break
            print(f"Patching Greenworks at '{path}'")
            ppath = path.parent
            # Unfortunately, overlayfs is currently incompatible with casefolding-enabled ext4.
            # Steam libraries are very likely to be on such a filesystem though.
            #overlayns.append("-o")
            #overlayns.append("{},shadow,lowerdir={},nodev,nosuid".format(ppath,r.nwjs_greenworks_path))
            # Instead, fall back to copies and bind mounts
            tempdir = proc.temp_dir(prefix=str(ppath.relative_to(game.root)).replace("/", "_"))
            xpath = tempdir.name
            if ',' in str(ppath) or ',' in str(xpath):
                self.app.show_error("Comma in paths is currently not supported by overlayns\nGreenworks support disabled")
                continue
            copytree(ppath, xpath)
            copytree(nwjs.get_path("greenworks"), xpath, dirs_exist_ok=True, copy_function=copy_unlink)
            proc.overlayns_bind(xpath, ppath)
        
        # TODO: make configurable
        bg_scripts = [self.base / 'injects/case-insensitive-nw.js']
        inject_scripts = []

        if game.rpgmaker_release in ("MV","MZ"):
            # Disable this if we can detect a rmmv  plugin that provides remapping?
            inject_scripts.append(self.base / 'injects/remap-mv.js')

        # Patch package json
        with open(game.package_json) as f:
            pkg = json.load(f)
        if nwjs.version >= (0, 19):
            if bg_scripts:
                pkg['bg-script'] = self._inject_file(game, proc, "preload", bg_scripts)
            if inject_scripts:
                pkg['inject_js_start'] = self._inject_file(game, proc, "inject", inject_scripts)
        else:
            if bg_scripts or inject_scripts:
                pkg['inject_js_start'] = self._inject_file(game, proc, "inject", bg_scripts + inject_scripts)
        with proc.temp_file(prefix="package-", suffix=".json") as f:
            json.dump(pkg, f)
            proc.overlayns_bind(f.name, game.package_json)

    def run(self, game, arguments: Sequence[str], nwjs_name=None, dry=False, sdk=None, no_overlayns=False) -> int:
        if not game.is_nwjs_app:
            raise RuntimeError("Called nwjs.Runtime.run with non-NW.js game")

        if not game.package_json:
            self.app.show_error(f"{game.root}\ndoesn't look like a RPGMaker MV/MZ (or other NW.js) game")
            return 3

        # Get suitable NW.js distro
        try:
            nwjs = self.select_and_download_nwjs(game, nwjs_name, sdk)
        except ErrorCode as e:
            return e.code

        proc = ProcessLaunchInfo(self.app, [nwjs.binary, game.package_dir, *arguments])

        # === Patch some game files ===
        if no_overlayns:
            self.app.show_warn("Overlayns is disabled. Plugin and Greenworks support not available.")
        else:
            self.overlay_files(game, nwjs, proc)

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
