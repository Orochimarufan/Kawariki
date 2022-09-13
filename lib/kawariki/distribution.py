from functools import cached_property
from json import load
from pathlib import Path
from typing import (ClassVar, Dict, Generic, List, Optional, Sequence, Tuple,
                    Type, TypedDict, TypeVar, Union)

from .misc import version_str

D = TypeVar("D", bound="Distribution")
DI = TypeVar("DI", bound="DistributionInfo")


class DistributionInfo(TypedDict, total=False):
    name: str               # Distribution name
    version: Sequence[int]  # Distribution version (required)
    platforms: Sequence[str]# Compatible platforms
    url: str                # Download URL (tar archive, required)
    binary: str             # Binary name
    alias: Sequence[str]    # Aliases for humans


class Distribution(Generic[DI]):
    info: DI
    path: Path
    platform: str

    dist_name: Optional[str] = None
    strip_leading: ClassVar[Union[bool, str]] = True
    fill_platform: ClassVar[bool] = False
    any_platform: ClassVar[bool] = False
    format_url: ClassVar[bool] = True
    default_binary_name: ClassVar[str]

    def __init__(self, info: DI, dist_path: Path, platform=None):
        if "platforms" in info:
            if platform is None:
                self.platform = info["platforms"][0]
            elif platform in info["platforms"]:
                self.platform = platform
            else:
                raise ValueError(f"Incompatible platform set: {info['platforms']}")
        elif platform is not None and self.fill_platform:
            self.platform = platform
        elif self.any_platform:
            self.platform = "any"
        else:
            raise ValueError(f"Missing platforms key in distribution {info}")

        if self.dist_name is None:
            self.dist_name = dist_path.name

        self.info = info
        self.path = dist_path / self.name

    @property
    def version(self) -> Tuple[int, ...]:
        # Return tuple for easy comparison with (1,4) version tuple literals
        return tuple(self.info["version"])

    @property
    def version_str(self) -> str:
        return version_str(self.info["version"])

    @cached_property
    def slug(self) -> str:
        return f"{self.dist_name}-{version_str(self.version)}-{self.platform}"

    @property
    def name(self) -> str:
        try:
            return self.info["name"]
        except KeyError:
            return self.slug

    @property
    def available(self) -> bool:
        return self.path.exists()

    @property
    def binary(self) -> Path:
        return self.path / (self.info["binary"] if "binary" in self.info else self.default_binary_name)

    @property
    def url(self) -> str:
        if "url" in self.info:
            if not self.format_url:
                return self.info["url"]
            url = self.info["url"].format(platform=self.platform)
        else:
            url = self.generate_url()
        self.__dict__["url"] = url
        return url

    def generate_url(self) -> str:
        raise NotImplementedError()

    def match(self, name: str) -> bool:
        return name in self.info["alias"] or name == self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} {version_str(self.version)} '{self.name}' at 0x{id(self):x}>"

    @classmethod
    def load(cls: Type[D], infos: Sequence[DI], dist_path: Path, platform: Optional[str] = None) -> List[D]:
        return [cls(i, dist_path, platform)
                for i in infos
                if platform is None or "platforms" not in i or platform in i["platforms"]]

    @classmethod
    def load_json(cls: Type[D], filename: Path, dist_path: Path, platform: Optional[str] = None) -> List[D]:
        with open(filename, "r") as f:
            return cls.load(load(f), dist_path, platform)
