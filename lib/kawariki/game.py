# :---------------------------------------------------------------------------:
#   Information about an installed game
# :---------------------------------------------------------------------------:

from functools import cached_property
from os import environ
from pathlib import Path
from re import compile as re_compile

from .misc import DetectedProperty
from .nwjs.package import PackageNw
from .renpy.detect import RenpyVersion

__all__ = ["Game"]


class Game:
    root: Path
    binary_name_hint: str|None

    def __init__(self, game_root: Path, binary_name_hint: str|None):
        self.root = game_root
        self.binary_name_hint = binary_name_hint

    # +-------------------------------------------------+
    # NW.js
    # +-------------------------------------------------+
    @cached_property
    def package_nw(self) -> PackageNw|None:
        return PackageNw.find(self.root, self.binary_name_hint)

    @property
    def is_nwjs_app(self) -> bool:
        # TODO: this is very broad
        return self.package_nw is not None

    # +-------------------------------------------------+
    # Engine detection
    # +-------------------------------------------------+
    # www/js/rpg_core.js, js/rmmz_core.js
    RPGMAKER_INFO_RE    = re_compile(r'''Utils.RPGMAKER_(VERSION|NAME)\s*\=\s*["']([^"']+)["']''')
    RPGMAKER_LIBRARY_RE = re_compile(r'''RGSS(\d+\w)(?:\.dll)?$''') # Game.ini[Game.Library]
    TYRANO_VERSION_RE   = re_compile(r'''(?<!\w)version:\s*(\d+),''') # tyrano/plugins/kag.js

    def detect(self):
        # Do all engine detection in a single run
        # Ensure all attributes are initialized to None
        self.rpgmaker_release = None
        self.rpgmaker_version = None
        self.rpgmaker_runtime = None
        self.tyrano_version = None

        # NW.js
        if pkg := self.package_nw:
            with pkg.open_fs() as fs:
                # Detect RPGMaker MV, MZ
                for candidate in ("/www/js/rpg_core.js", "/js/rmmz_core.js"):
                    if fs.exists(candidate):
                        content = fs.read_text(candidate)
                        for m in self.RPGMAKER_INFO_RE.finditer(content):
                            if m.group(1) == "VERSION":
                                self.rpgmaker_version = tuple(int(x) for x in m.group(2).split('.'))
                            elif m.group(1) == "NAME":
                                self.rpgmaker_release = m.group(2)

                # Detect Tyrano Builder
                if fs.exists("/tyrano/plugins/kag/kag.js"): # noqa: SIM102
                    if m := self.TYRANO_VERSION_RE.search(fs.read_text("/tyrano/plugins/kag/kag.js")):
                        self.tyrano_version = m.group(1)

        # Detect legacy RPGMaker (RGSS)
        game_ini = self.root / "Game.ini" # TODO: perform search?
        if game_ini.exists():
            from configparser import ConfigParser
            cfg = ConfigParser()
            cfg.read(game_ini, "sjis") # TODO: encoding
            self._detect_rgss_version(cfg["Game"]["Library"])
            self.rpgmaker_runtime = cfg.get("Game", "RTP", fallback=None)
        else:
            for dllname in self.root.rglob("RGSS*.dll"):
                self._detect_rgss_version(dllname.name)

    def _detect_rgss_version(self, dllname):
        if m := self.RPGMAKER_LIBRARY_RE.search(dllname):
            vt = tuple(int(d) if d.isdigit() else d for d in m.group(1))
            if isinstance(vt[0], int) and vt[0] >= 1 and vt[0] <= 3:
                self.rpgmaker_release = ("XP", "VX", "VXAce")[vt[0]-1]
                self.rpgmaker_version = vt

    # +-------------------------------------------------+
    # RPGMaker
    # +-------------------------------------------------+
    rpgmaker_release = DetectedProperty[str|None](detect)
    rpgmaker_version = DetectedProperty[tuple[int|str, ...]|None](detect)
    rpgmaker_runtime = DetectedProperty[str|None](detect)

    @property
    def is_rpgmaker(self) -> bool:
        return self.rpgmaker_release is not None

    @property
    def is_rpgmaker_rgss(self) -> bool:
        return self.rpgmaker_release in ("VXAce", "VX", "XP")

    @property
    def is_rpgmaker_nwjs(self) -> bool:
        return self.rpgmaker_release in ("MV", "MZ")

    @property
    def is_rpgmaker_mv_legacy(self) -> bool|None:
        # Check for old RPGMaker MV version. Assume missing version means legacy
        return self.rpgmaker_release == "MV" and (self.rpgmaker_version is None or self.rpgmaker_version < (1, 6))

    # +-------------------------------------------------+
    # Tyrano Script
    # +-------------------------------------------------+
    tyrano_version = DetectedProperty[int|None](detect)

    # +-------------------------------------------------+
    # Ren'Py
    # +-------------------------------------------------+
    @cached_property
    def renpy_version(self) -> RenpyVersion|None:
        return RenpyVersion.find(self.root)

    @property
    def is_renpy(self) -> bool:
        return self.renpy_version is not None

    # +-------------------------------------------------+
    # Godot
    # +-------------------------------------------------+
    @cached_property
    def godot_pack(self) -> Path|None:
        # TODO: support merged exe, heuristics?
        if self.binary_name_hint is None:
            return None
        exe = self.root / self.binary_name_hint
        pck = exe.with_suffix(".pck")
        if pck.exists():
            return pck
        if exe.suffix in {'.exe', ".x86_64"}:
            from .godot.pack import PackReader
            try:
                with open(exe, 'rb') as f:
                    PackReader.find_offset(f)
            except ValueError:
                pass
            else:
                return exe
        return None

    @property
    def is_godot(self) -> bool:
        return self.godot_pack is not None

    # +-------------------------------------------------+
    # Steam meta-information
    # +-------------------------------------------------+
    @cached_property
    def steam_appid(self) -> str|None:
        if "SteamAppId" in environ:
            return environ["SteamAppId"]
        appid_txt = self.root / "steam_appid.txt"
        if appid_txt.is_file():
            return appid_txt.read_text("ascii")
        return None
