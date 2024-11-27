import json
import os
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager, suppress
from functools import cached_property
from pathlib import Path
from shlex import split as shlex_split
from shutil import copytree
from tempfile import NamedTemporaryFile
from typing import IO, ClassVar, Literal, TypedDict

from ..app import App, IRuntime
from ..distribution import Distribution, DistributionInfo, DistributionInfoProperty, DistributionInfoPropertyOptional, get_first
from ..game import Game
from ..misc import ErrorCode, copy_unlink, version_str
from ..process import ProcessLaunchInfo
from ..utils.textwrap import dedent, indent
from ..utils.html import HTMLBuilder, HTMLScriptsPatcher
from .package import PackageNw


class NWjsDistributionInfo(DistributionInfo):
    sdk: bool


class GreenworksDistInfo(DistributionInfo, TypedDict('_GreenworksDistInfo', {
        'steamworks-url': str,      # Steamworks download URL
    }), total=False):
    nwjs: Sequence[Sequence[int]]   # Required
    steamworks: Sequence[int]       # Steamworks version


class NWjs(Distribution):
    """ A distribution of NW.js """
    info: NWjsDistributionInfo

    @property
    def is_sdk(self) -> bool:
        """ Whether distribution includes SDK features """
        return self.info.get("sdk", False)

    @classmethod
    def load_variants(cls, info: NWjsDistributionInfo, dist_path: Path, platform=None,
                      platform_map: dict[str, str]|None=None,
                      templates: dict[str, NWjsDistributionInfo]={}):
        """ Synthesize sdk and non-sdk variants if sdk=synthesize """
        template_seq = cls._build_template_order(info, templates)
        infos: Sequence[NWjsDistributionInfo]
        if info.get('sdk', get_first('sdk', template_seq, None)) == "synthesize":
            alias: Sequence[str] = info.get('alias', [])
            # TypedDict.update seems to have some typing issues
            info_sdk = info.copy()
            info_sdk.update(sdk=True, alias=[*alias, *(f"{a}-sdk" for a in alias)]) #type: ignore[call-arg]
            info_nosdk = info.copy()
            info_nosdk.update(sdk=False, alias=[*alias, *(f"{a}-nosdk" for a in alias)]) #type: ignore[call-arg]
            infos = (info_nosdk, info_sdk)
        else:
            infos = (info,)
        return (cls(info, dist_path, platform, platform_map, template_seq) for info in infos)


class GreenworksDistribution(Distribution):
    """ A distribution of Greenworks for NW.js """
    info: GreenworksDistInfo

    @property
    def nwjs_version(self) -> tuple[int, ...]:
        """ The first compatible NW.js version """
        return tuple(self.info["nwjs"][0])

    def is_compatible(self, nwjs: NWjs) -> bool:
        """ Check whether this Greenworks distribution works with a specific NW.js version """
        return any(nwjs.version[:len(ver)] == tuple(ver) for ver in self.info["nwjs"])

    steamworks_version = DistributionInfoPropertyOptional[str]("steamworks", version_str)
    steamworks_url = DistributionInfoPropertyOptional[str]("steamworks-url")
    steamworks_platform = DistributionInfoProperty[str]("steamworks-platform")

    def lib_filename(self, libname) -> str:
        if self.steamworks_platform.startswith("linux"):
            return f"lib{libname}.so"
        if self.steamworks_platform == "osx":
            return f"lib{libname}.dylib"
        if self.steamworks_platform == "win64":
            return f"{libname}64.dll"
        if self.steamworks_platform == "win32":
            return f"{libname}.dll"
        raise RuntimeError(f"Unknown Steamworks platform: {self.steamworks_platform}")

    def is_steamworks_included(self) -> bool:
        return (self.path / "lib" / self.lib_filename("steam_api")).exists()


def overlay_or_clobber(pkg: PackageNw, proc: ProcessLaunchInfo,
                       filename: str, mode: Literal["a", "w"]="w") -> AbstractContextManager[IO[str]]:
    """ Clobber file if pkg.may_clobber, otherwise use proc.replace_file  to overlay """
    path = pkg.path / filename
    if pkg.may_clobber:
        return path.open(mode)
    return proc.replace_file(path, mode)


class JSImportMap(TypedDict, total=False):
    imports: dict[str, str]
    scopes: dict[str, dict[str, str]]


def importmap_get_scope(map: JSImportMap, scope: str|None=None) -> dict[str, str]:
    """ Get or create importmap scope """
    if scope:
        scopes = map.setdefault("scopes", {})
        return scopes.setdefault(scope, {})
    else:
        return map.setdefault("imports", {})


js = json.dumps
NL = '\n'


class InjectFileBuilder:
    rt: 'Runtime'
    nwjs: NWjs

    # inject = inject_js_start, preload = bg_script package.json keys
    Context = Literal["inject", "preload"]
    Type = Literal["import", "system", "require", "eval", "script", "module"]

    class Script(TypedDict):
        context: Sequence['InjectFileBuilder.Context']
        type: 'InjectFileBuilder.Type'
        src: str

    scripts: list[Script]
    importmap: dict[str, Path]
    importmap_r: dict[Path, str]

    _missing: Callable[[Path], None]

    def __init__(self, rt: 'Runtime', nwjs: NWjs):
        self.rt = rt
        self.nwjs = nwjs

        self.scripts = []
        self.importmap = {
            "$kawariki:es-polyfill": self.es_path / f"{self.es_tag}-polyfill.mjs",
            "$kawariki:es/": self.es_path,
        }
        self.importmap_r = {p: k for k, p in self.importmap.items()}

        self._missing = self._notfound_error

    def __bool__(self):
        return bool(self.scripts)

    def has_scripts_for(self, contexts: Sequence[Context]) -> bool:
        return any(ctx in script["context"] for ctx in contexts for script in self.scripts)

    def __add__(self, other: 'InjectFileBuilder') -> 'InjectFileBuilder':
        new = InjectFileBuilder(self.rt, self.nwjs)
        new.scripts = [*self.scripts, *other.scripts]
        new.importmap = self.importmap.copy()
        new.importmap.update(other.importmap)
        new.importmap_r = self.importmap_r.copy()
        new.importmap_r.update(other.importmap_r)
        return new

    def __iadd__(self, other: 'InjectFileBuilder'):
        self.scripts.extend(other.scripts)
        self.importmap.update(other.importmap)
        self.importmap_r.update(other.importmap_r)

    def clear(self):
        self.scripts.clear()
        self.importmap.clear()
        self.importmap_r.clear()

    #### Engine capabilities ####
    # Supported ECMAScript levels with minimum NW.js version
    # Every level has it's own transpiled scripts in 'js/es{level}'
    ES_LEVELS = (
        # ES13 (2022) supported since NW.js 0.57 (Chromium 94)
        ((0, 57), 13),
        # Only support down to NW.js 0.12 (required by old RMMV versions)
        ((0, 12), 5),
    )

    @cached_property
    def es_level(self) -> int:
        """ The highest ECMAScript level supported by the NW.js distro """
        for min_nwjs_version, es in self.ES_LEVELS:
            if self.nwjs.version >= min_nwjs_version:
                return es
        return 0

    @property
    def es_tag(self) -> str:
        return f"es{self.es_level}"

    @property
    def es_path(self) -> Path:
        """ The path to the compiled files for the current ES level """
        return self.rt.base_path / 'js' / self.es_tag

    @property
    def has_es_modules(self) -> bool:
        # Dynamic import introduced in ES11 (2020)
        return self.es_level >= 11

    #### Modules & ImportMaps ####
    def map(self, name: str, path: Path):
        self.importmap[name] = path
        self.importmap_r[path] = name

    def _map_module(self, path: Path) -> str:
        if name := self.importmap_r.get(path):
            return name
        if ns := self.importmap_r.get(path.parent):  # noqa: SIM102
            if ns.endswith('/'):
                return f"{ns}{path.name}"
        return f"file://{path}"

    def _notfound_error(self, path: Path):
        raise FileNotFoundError(path)

    def module(self, path: Path|str, context: Sequence[Context]=("inject",)):
        """ Inject an ES Module """
        src = None
        if isinstance(path, str):
            src = f"$kawariki:es/{path}"
            path = self.es_path / path
        if not path.exists():
            return self._missing(path)
        elif src is None:
            src = self._map_module(path)
        if any(c != "inject" for c in context):
            raise ValueError("Modules aren't supported for preload (yet)")
        self.scripts.append({
            "context": context,
            "type": "import" if self.has_es_modules else "system",
            "src": src,
        })

    @property
    def importmap_json(self) -> JSImportMap:
        """ The import map as JSON object """
        return {
            "imports": {k: f"file://{path}{'/' if k.endswith('/') else ''}" for k, path in self.importmap.items()}
        }

    #### Legacy Scripts & Code ####
    def script(self, path: Path|str):
        """ Inject as script tag (inject only) """
        if isinstance(path, str):
            path = self.es_path / path
        if not path.exists():
            return self._missing(path)
        self.scripts.append({
            "context": ("inject",),
            "type": "script",
            "src": f"file://{path}"
        })

    def require(self, path: Path, context: Sequence[Context]=("preload",)):
        """ Inject a require() call (Nodejs)"""
        if not path.exists():
            return self._missing(path)
        self.scripts.append({
            "context": context,
            "type": "require",
            "src": str(path),
        })

    def eval(self, source: str, context: Sequence[Context]=("inject",)):
        self.scripts.append({
            "context": context,
            "type": "eval",
            "src": source,
        })

    #### JS generation ####
    INJECTORS: ClassVar[dict[Type, Callable[[Script], str]]] = {
        "import":   lambda s: f"promises.push(import({js(s["src"])}));",
        "system":   lambda s: f"promises.push(System.import({js(s["src"])}));",
        "require":  lambda s: f"require({js(s["src"])});",
        "eval":     lambda s: f"(function(){{{indent(s["src"], '    ', skip_first=True)}}})();",
        "script":   lambda s: f"appendScript({js(s|{'type': 'text/javascript'})});",
        "module":   lambda s: f"appendScript({js(s)});",
    }

    def write_inner(self, file: IO[str], contexts: Sequence[Context], *,
                    embedded_module: bool=False, ilevel: str="    "):
        if "inject" in contexts or embedded_module:
            file.write(dedent(f"""\
                    var script_parent = document.{'body' if embedded_module else 'head'};
                    function appendScript(attrs, onload, onerror) {{
                        var el = document.createElement("script");
                        el.async = false;
                        for (var attr in attrs)
                            el[attr] = attrs[attr];
                        if (onload !== undefined)
                            el.addEventListener("load", onload);
                        if (onerror !== undefined)
                            el.addEventListener("error", onerror);
                        script_parent.appendChild(el);
                        return el;
                    }}
                """, ilevel))
        omit_keys = {"context"}
        scripts: list[InjectFileBuilder.Script] = [
                {k: v for k, v in script.items() if k not in omit_keys} # type: ignore
                   for script in self.scripts
                   if any(ctx in script["context"] for ctx in contexts)]
        injectors = [self.INJECTORS[s["type"]](s) for s in scripts]
        if "inject" in contexts:
            parts: list[str] = []
            if not embedded_module:
                parts += (
                    "// Import Map",
                    f"var importmap = {js(self.importmap_json, indent=2)};\n"
                )
            if self.has_es_modules:
                # Add importmap to DOM. <script type=importmap> doesn't seem to fire load event
                if not embedded_module:
                    parts.append('appendScript({type: "importmap", textContent: JSON.stringify(importmap)});')
                parts += (
                    "// Injected scripts",
                    "var promises = [];",
                    *injectors,
                )
                if embedded_module:
                    parts.append("await Promise.allSettled(promises);")
            else:
                # Use s.js
                parts += (
                    f'appendScript({{type: "text/javascript", src: "file://{self.es_path / "s.js"}"}}, function () {{',
                    "    System.addImportMap(importmap);",
                    "    // Injected scripts",
                    *(indent(i, '    ') for i in injectors),
                    "});"
                )
            file.write(f"{indent(NL.join(parts), ilevel)}\n")
        else:
            # Preload only, no modules support
            file.write(f"{indent(NL.join(injectors), ilevel)}\n")

    def write(self, file: IO[str], contexts: Sequence[Context]):
        """ Build a file for inject_js_start or bg_script keys """
        file.write("(function() {\n")
        self.write_inner(file, contexts)
        file.write("})();\n")

    ### HTML Generation ###
    class HTMLPatcher(HTMLScriptsPatcher):
        HSE_ATTRS: ClassVar[dict[type[str]|type[bool], dict[str, str]]] = {
            str: {
                "src": "src",
                "$src": "text",
                "attributionsrc": "attributionSrc",
                "blocking": "blocking",
                "charset": "charset",
                "fetchpolicy": "fetchPolicy",
                "integrity": "integrity",
                "referrerpolicy": "referrerPolicy",
            },
            bool: {
                "async": "async",
                "defer": "defer",
                "nomodule": "noModule",
            }
        }

        def __init__(self, parent: 'InjectFileBuilder', file: IO[str], contexts: Sequence['InjectFileBuilder.Context']):
            super().__init__(HTMLBuilder(file))
            self.parent: InjectFileBuilder = parent
            self.contexts = contexts

        def write_scripts(self, scripts: list[dict[str, str|None]]):
            html = self.output
            html.comment("Kawariki NW.js")
            # Hoist and merge import map
            importmap = self.parent.importmap_json
            for script in reversed([script for script in scripts if script.get("type") == "importmap"]):
                text = script.get("$src")
                if not text:
                    continue
                map: JSImportMap = json.loads(text)
                for scopename in None, *map.get("scopes", {}).keys():
                    scope = importmap_get_scope(importmap, scopename)
                    scope.update({
                        name: url for name, url in importmap_get_scope(map, scopename).items()
                        if name not in scope
                    })
            html.leaf("script", {"type": "importmap"}, json.dumps(importmap, indent=2))
            # Add preamble
            html.begin("script", {"type": "module"})
            html.write('console.log("[Kawariki:NewLoader] Setting up Kawariki NW.js runtime");')
            self.parent.write_inner(html.file, self.contexts, embedded_module=True, ilevel=html.indent_prefix)
            # Add scripts
            scriptlines = [
                "import {Logger} from '$kawariki:es/logger.mjs';",
                "const log = new Logger('Kawariki:NewLoader', {color: 'grey'});",
                "log.info('Loading Application...');",
                # RPGMaker needs window.load event to function
                # When loading it asynchronously this way, it's already been fired,
                # so do it manually
                "// Setup script load tracking",
                "import {global} from '$kawariki:es/scriptobserver.mjs';"
                "let observer = global();",
                "observer.on('settled', function onSettled() {",
                "    observer.off('settled', onSettled);",
                "    const fail = observer.errors > 0;",
                "    if (fail) log.error('Failed loading application scripts:', observer.errors, '/', observer.count);",
                "    else log.info('Finished loading scripts:', observer.count);",
                "    window.dispatchEvent(new Event(fail ? 'error' : 'load'));",
                "});",
                "observer.observe();",
                "// Load hoisted scripts",
                "let loading = [];",
                "function loadScript(script) {",
                "    loading.push(new Promise((res, rej) => appendScript(script, res, rej)));",
                "};",
            ]
            for script in scripts:
                scripttype = script.get("type") or "text/javascript"
                if scripttype == "importmap":
                    continue
                attrs: dict[str, str|bool] = {"type": scripttype}
                for key, attr in self.HSE_ATTRS[str].items():
                    if (val := script.get(key)) is not None:
                        attrs[attr] = val
                for key, attr in self.HSE_ATTRS[bool].items():
                    if key in script:
                        attrs[attr] = True
                scriptlines.append(f"loadScript({js(attrs)});")
            scriptlines += (
                "Promise.all(loading).then(",
                "     ok => log.debug('Finished loading hoisted scripts:', loading.length),",
                "     err => log.error('Failed to load hoisted scripts'),",
                ");"
            )
            html.write("\n".join(scriptlines))
            html.end('script')
            html.comment("Kawariki NW.js end")

    def write_html(self, infile: IO[str], outfile: IO[str], contexts: Sequence[Context]=("inject",), *, bufsize=16384):
        """ Patch NW.js main.html """
        patcher = self.HTMLPatcher(self, outfile, contexts)
        while True:
            chunk = infile.read(bufsize)
            if not chunk:
                return
            patcher.feed(chunk)


class Runtime(IRuntime):
    """ Kawariki runtime for NW.js based games """
    app: App
    base_path: Path
    overlayns_bin: Path
    nwjs_dist_path: Path
    greenworks_dist_path: Path

    def __init__(self, app: App):
        self.app = app
        self.base_path = app.app_root / "nwjs"
        self.overlayns_bin = app.app_root / "overlayns-static"
        self.nwjs_dist_path = app.dist_path / "nwjs"
        self.greenworks_dist_path = app.dist_path / "nwjs-greenworks"
        self.steamworks_dist_path = app.dist_path / "steamworks"

    # +-------------------------------------------------+
    # NW.js versions
    # +-------------------------------------------------+
    @cached_property
    def nwjs_versions(self) -> Sequence[NWjs]:
        """ All compatible distributions of NW.js from versions.json """
        return NWjs.load_json(self.base_path / "versions.json", self.nwjs_dist_path, self.app.platform)

    def get_nwjs(self, version_name: str) -> NWjs|None:
        """ Get a specific NW.js distribution by alias """
        for ver in self.nwjs_versions:
            if ver.match(version_name):
                return ver
        return None

    def get_nwjs_version(self,
                         minver: tuple[int, ...]|None=None,
                         maxver: tuple[int, ...]|None=None,
                         sdk: bool|None=None) -> NWjs|None:
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

    def select_nwjs_version(self, game: Game, nwjs_name: str|None=None, sdk: bool|None=False) -> NWjs:
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

    def select_and_download_nwjs(self, game: Game, nwjs_name: str|None=None, sdk: bool|None=False) -> NWjs:
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

    def try_get_greenworks(self, nwjs: NWjs) -> GreenworksDistribution|None:
        """ Select and download a Greenworks distribution compatible with a NW.js distribution """
        for gw in self.greenworks_versions:
            if gw.is_compatible(nwjs):
                break
        else:
            self.app.show_warn(f"No Greenworks available for NW.js version {nwjs.version_str} ({nwjs.name})."
                " Continuing without Steamworks Support")
            return None
        if not gw.available:
            from ..download import download_dist_progress_archive
            download_dist_progress_archive(self.app, gw)
            self.app.show_info(f"Downloaded {gw.name}")
        if not gw.is_steamworks_included():
            # Get steamworks
            if not self.steamworks_dist_path.exists():
                self.steamworks_dist_path.mkdir()
            url = gw.info['steamworks-url']
            filename = url.rsplit('/', 2)[-1]
            filepath = self.steamworks_dist_path / filename
            if not filepath.exists():
                self.app.show_info(dedent(f"""
                    For Steamworks to function with the Kawariki NW.js runtime,
                    a matching version of the Steamworks redistributable libraries must be used.

                    Please download Steamworks SDK {version_str(gw.info['steamworks'])} from Valve:
                    {url}

                    And place it in {self.steamworks_dist_path}, then click OK"""), title="Kawariki Steamworks Support")
                if not filepath.exists():
                    self.app.show_error(f"{filename} not found. Continuing without Steamworks Support")
                    return None
            # Unpack libs to greenworks dist
            from ..fs.zip import ZipFs
            from ..fs.util import copy_from
            libdir = gw.path / "lib"
            with ZipFs(filepath) as sw:
                copy_from(sw.root / "sdk/public/steam/lib" / gw.steamworks_platform /
                    gw.lib_filename("sdkencryptedappticket"), libdir)
                copy_from(sw.root / "sdk/redistributable_bin" / gw.steamworks_platform /
                    gw.lib_filename("steam_api"), libdir)
            if not gw.is_steamworks_included():
                self.app.show_error(f"Failed to add Steamworks SDK to {gw.name}. Continuing without Steamworks Support")
                return None
        return gw

    # +-------------------------------------------------+
    #   Run NW.js for Game
    # +-------------------------------------------------+
    def _inject_file(self,
                     pkg: PackageNw,
                     proc: ProcessLaunchInfo,
                     inject: InjectFileBuilder,
                     mode: Sequence[InjectFileBuilder.Context],
                     patch_html: Path|None=None):
        """ Create a file to be set as bg_script/inject """
        parent, prefix, suffix = pkg.path, f"{'-'.join(mode)}-", ".js"
        if patch_html:
            parent, prefix, suffix = patch_html.parent, "main-" + prefix, ".html"
        with NamedTemporaryFile("w", dir=parent, prefix=prefix, suffix=suffix, delete=False) as f:
            name = str(Path(f.name).relative_to(pkg.path))
            if not patch_html:
                f.write(f"// Kawariki NW.js {' and '.join(mode)} script\n")
                f.write(f"console.log('[Kawariki] Injecting {name}');\n")
            try:
                if not patch_html:
                    inject.write(f, mode)
                else:
                    with patch_html.open('r') as fin:
                        inject.write_html(fin, f, mode)
            except:
                os.unlink(f.name)
                raise
            proc.at_cleanup(lambda: os.unlink(f.name))
            return name

    def overlay_greenworks(self, pkg: PackageNw, nwjs: NWjs, proc: ProcessLaunchInfo):
        """ Overlay appropriate Greenworks binaries over package """
        for path in pkg.path.rglob("greenworks.js"):
            greenworks = self.try_get_greenworks(nwjs)
            if not greenworks:
                break
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
            # Instead, fall back to individual bind mounts
            for parent_, _, files in os.walk(greenworks.path):
                parent = Path(parent_)
                pparent = ppath / parent.relative_to(greenworks.path)
                for fn in files:
                    proc.replace_file_from(pparent / fn, parent / fn)

    def overlay_files(self, game: Game, pkg: PackageNw, nwjs: NWjs, proc: ProcessLaunchInfo):
        if pkg.is_archive:
            raise RuntimeError("Cannot modify archived package directly")

        # Patch native greenworks (Steamworks API)
        if not os.environ.get("KAWARIKI_NWJS_NO_GREENWORKS"):
            self.overlay_greenworks(pkg, nwjs, proc)

        # TODO: make all this configurable
        conf = pkg.read_json()

        inject = InjectFileBuilder(self, nwjs)
        inject._missing = lambda path: print(f"Note: Script {path.name} not found. "
                                             f"It may not be compatible with NW.js v{nwjs.version_str}")

        js = self.base_path / 'js'

        if game.is_rpgmaker:
            inject.require(js / 'case-insensitive-nw.js', ('inject',))
        else:
            inject.require(js / 'case-insensitive-nw.js', ('preload',))

        if game.rpgmaker_release in ("MV", "MZ"):
            # Disable this if we can detect a rmmv  plugin that provides remapping?
            inject.module("rpg-remap.mjs")
            inject.module("rpg-fixes.mjs")
            inject.module("rpg-vars.mjs")
            if os.environ.get("KAWARIKI_NWJS_RPG_DECRYPTED_ASSETS"):
                if game.is_rpgmaker_mv_legacy or game.rpgmaker_release not in ("MV", "MZ"):
                    self.app.show_warn("RPGMaker version isn't supported for KAWARIKI_NWJS_RPG_DECRYPTED_ASSETS")
                else:
                    inject.script(js / f"{game.rpgmaker_release.lower()}-decrypted-assets.js")

        # User scripts
        userscript_dir = pkg.enclosing_directory.absolute()
        inject.map('$kawariki:pkgparent/', userscript_dir)
        for userscript in userscript_dir.glob("*.kawariki.js"):
            print(f"Found UserScript {userscript}")
            inject.script(userscript)
        for userscript in userscript_dir.glob("*.kawariki.mjs"):
            print(f"Found UserScript {userscript}")
            inject.module(userscript)

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
                        if end > start:
                            conf["name"] = html[start:end]

        if os.environ.get("KAWARIKI_NWJS_DEVTOOLS"):
            inject.eval(dedent("""\
                window.setTimeout(function(){
                    (nw !== undefined ? nw : require("nw.gui")).Window.get().showDevTools();
                }, 100);"""))

        # Patch package json
        if nwjs.version >= (0, 19):
            def add_pkg_script(key: str, contexts: Sequence[InjectFileBuilder.Context], patch_html: bool=False):
                if inject.has_scripts_for(contexts):
                    patch = pkg.path/conf[key] if patch_html else None
                    conf[key] = self._inject_file(pkg, proc, inject, contexts, patch_html=patch)
            inject_contexts: Sequence[InjectFileBuilder.Context] = "inject",
            use_preload = not os.environ.get("KAWARIKI_NWJS_INJECT_BG")
            if use_preload:
                add_pkg_script("bg_script", ("preload",))
            else:
                inject_contexts = "preload", *inject_contexts
            if nwjs.version >= (0, 70) and conf.get("main"):
                # Need to patch main.html to ensure loading order
                add_pkg_script("main", inject_contexts, patch_html=True)
            else:
                add_pkg_script("inject_js_start", inject_contexts)
        else:
            if inject:
                #modify main.html
                with open(pkg.path / conf["main"]) as f:
                    html = f.read()
                fn = self._inject_file(pkg, proc, inject, ("inject", "preload"))
                html = html.replace("<head>", f"""<head><script src="file://{os.path.realpath(fn)}"></script>""")
                with overlay_or_clobber(pkg, proc, conf["main"]) as f:
                    f.write(html)

        # Don't disable DevTools
        conf['chromium-args'] = conf.get('chromium-args', "").replace("--disable-devtools", "")
        # Default to Wayland on NW.js >= 0.75 (arbitrarily chosen)
        if os.environ.get('WAYLAND_DISPLAY') and nwjs.version >= (0, 75):
            conf['chromium-args'] = "--ozone-platform=wayland " + conf.get('chromium-args', "")

        with overlay_or_clobber(pkg, proc, pkg.json) as f:
            json.dump(conf, f)

    def run(self, game, arguments: Sequence[str], *,
            nwjs_name: str|None=None, dry=False, sdk: bool|None=None,
            no_overlayns=False, no_unpack=False,
            **kwds) -> int:
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

        nwjs_args = shlex_split(os.environ.get('KAWARIKI_NWJS_ARGS', ''))

        path = pkg.path.relative_to(game.root) if pkg.path.is_relative_to(game.root) else pkg.path.resolve()
        proc.argv.extend([*nwjs_args, path, *arguments])
        proc.workingdir = game.root

        # === Patch some game files ===
        self.overlay_files(game, pkg, nwjs, proc)

        # Custom overlays
        ons = pkg.enclosing_directory / "kawariki.overlayns"
        if ons.exists():
            if not proc.have_overlayns:
                self.app.show_warn("Found kawariki.overlayns file but overlayns isn't available")
            else:
                proc.add_overlays_from_file(ons)

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
