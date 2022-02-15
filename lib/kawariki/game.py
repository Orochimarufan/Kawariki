# :---------------------------------------------------------------------------:
#   Information about an installed game
# :---------------------------------------------------------------------------:

from functools import cached_property
from pathlib import Path
from re import compile as re_compile
from typing import Optional, Tuple

__all__ = ["Game"]


class Game:
    root: Path
    binary_name_hint: Optional[str]

    def __init__(self, game_root: Path, binary_name_hint: Optional[str]):
        self.root = game_root
        self.binary_name_hint = binary_name_hint

    # +-------------------------------------------------+
    # NW.js detection
    # +-------------------------------------------------+
    @cached_property
    def package_json(self) -> "Optional[Path]":
        if (p := self.root / "package.json").exists():
            return p
        elif (p := self.root / "www" / "package.json").exists():
            return p
        else:
            # Try to find package.json
            for p in self.root.rglob("package.json"):
                print(f"Using non-standard package.json location {p}")
                return p
        return None

    @property
    def package_dir(self) -> "Optional[Path]":
        """ Directory containing package.json, relative to game root """
        if pkg := self.package_json:
            return pkg.parent.relative_to(self.root)
        return None

    @property
    def is_nwjs_app(self) -> bool:
        # TODO: this is very broad
        return self.package_json is not None

    # +-------------------------------------------------+
    # RPGMaker detection
    # +-------------------------------------------------+
    RPGMAKER_INFO_RE = re_compile(r'''Utils.RPGMAKER_(VERSION|NAME)\s*\=\s*["']([^"']+)["']''')

    @cached_property
    def rpgmaker_info(self) -> "Optional[Tuple[str, Tuple]]":
        # Find RPGMaker core file
        # MV: rpg_core.js, MZ: rmmz_core.js
        for rpgcore in self.root.rglob("r*_core.js"):
            with open(rpgcore, "r") as f:
                kind = version = None
                for l in f:
                    if m := self.RPGMAKER_INFO_RE.search(l):
                        if m.group(1) == "VERSION" :
                            version = tuple(int(x) for x in m.group(2).split('.'))
                        elif m.group(1) == "NAME":
                            kind = m.group(2)
                        if version is not None and kind is not None:
                            return kind, version
        # Detect legacy RPGMaker (RGSS)
        for dllname in self.root.rglob("RGSS*.dll"):
            ver = dllname.name[4:].rsplit(".", 1)[0]
            if ver == "301":
                return "VXAce", (3,0,1)
            if ver == "300":
                return "VXAce", (3,0,0)
            if ver == "104E":
                return "XP", (1,0,4,'e')
            print(f"Looks like old RPGMaker, but not implemented: {dllname}")
        return None

    @property
    def rpgmaker_release(self) -> "Optional[str]":
        if i := self.rpgmaker_info:
            return i[0]
        return None

    @property
    def rpgmaker_version(self) -> "Optional[Tuple]":
        if i := self.rpgmaker_info:
            return i[1]
        return None

    @property
    def is_rpgmaker(self) -> bool:
        return self.rpgmaker_info is not None

    @property
    def is_rpgmaker_rgss(self) -> bool:
        return self.rpgmaker_release in ("VXAce", "VX", "XP")

    @property
    def is_rpgmaker_nwjs(self) -> bool:
        return self.rpgmaker_release in ("MV", "MZ")

    @property
    def is_rpgmaker_mv_legacy(self) -> "Optional[bool]":
        # Check for old RPGMaker MV version
        if i := self.rpgmaker_info:
            return i[0] == "MV" and i[1] < (1, 6)
        return None
