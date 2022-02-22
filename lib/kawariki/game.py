# :---------------------------------------------------------------------------:
#   Information about an installed game
# :---------------------------------------------------------------------------:

from functools import cached_property
from pathlib import Path
from re import compile as re_compile
from typing import Optional, Tuple

from .misc import DetectedProperty
from .nwjs.package import PackageNw

__all__ = ["Game"]


class Game:
    root: Path
    binary_name_hint: Optional[str]

    def __init__(self, game_root: Path, binary_name_hint: Optional[str]):
        self.root = game_root
        self.binary_name_hint = binary_name_hint

    # +-------------------------------------------------+
    # NW.js
    # +-------------------------------------------------+
    @cached_property
    def package_nw(self) -> Optional[PackageNw]:
        return PackageNw.find(self.root, self.binary_name_hint)

    @property
    def is_nwjs_app(self) -> bool:
        # TODO: this is very broad
        return self.package_nw is not None

    # +-------------------------------------------------+
    # Engine detection
    # +-------------------------------------------------+
    RPGMAKER_INFO_RE    = re_compile(r'''Utils.RPGMAKER_(VERSION|NAME)\s*\=\s*["']([^"']+)["']''') # rpg_core.js/rmmz_core.js
    TYRANO_VERSION_RE   = re_compile(r'''(?<!\w)version:\s*(\d+),''') # tyrano/plugins/kag.js

    def detect(self):
        # Do all engine detection in a single run
        # Ensure all attributes are initialized to None
        self.rpgmaker_release = None
        self.rpgmaker_version = None
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
                if fs.exists("/tyrano/plugins/kag/kag.js"):
                    if m := self.TYRANO_VERSION_RE.search(fs.read_text("/tyrano/plugins/kag/kag.js")):
                        self.tyrano_version = m.group(1)

        # Detect legacy RPGMaker (RGSS)
        # TODO: parse Game.ini for Library=
        for dllname in self.root.rglob("RGSS*.dll"):
            ver = dllname.name[4:].rsplit(".", 1)[0]
            vt = tuple(int(d) if d.isdigit() else d for d in ver)
            if isinstance(vt[0], int) and vt[0] >= 1 and vt[0] <= 3:
                self.rpgmaker_release = ("XP", "VX", "VXAce")[vt[0]]
                self.rpgmaker_version = vt

    # +-------------------------------------------------+
    # RPGMaker
    # +-------------------------------------------------+
    rpgmaker_release = DetectedProperty[Optional[str]](detect)
    rpgmaker_version = DetectedProperty[Optional[Tuple[int, ...]]](detect)

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
    def is_rpgmaker_mv_legacy(self) -> "Optional[bool]":
        # Check for old RPGMaker MV version
        return self.rpgmaker_release == "MV" and self.rpgmaker_version is not None and self.rpgmaker_version < (1, 6)

    # +-------------------------------------------------+
    # Tyrano Script
    # +-------------------------------------------------+
    tyrano_version = DetectedProperty[Optional[int]](detect)
