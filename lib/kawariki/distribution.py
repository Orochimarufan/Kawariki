from collections import ChainMap
from functools import cached_property
from json import load as json_load
from pathlib import Path
from typing import (Any, Callable, ClassVar, Dict, Generic, List, Optional,
                    Sequence, Tuple, Type, TypedDict, TypeVar, Union)

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
    strip_leading: str      # Strip leading component from archive filename

class DistributionList(TypedDict, total=False): # Generic[DI], unsupported w/ TypedDict until 3.11
    name: str                                   # Required; Name of folder inside dist/
    platforms: Union[List[str], Dict[str, str]] # Bounding set of supported platforms with renames
    default: DistributionInfo                   # Default values for all versions
    versions: Sequence[DistributionInfo]        # Required; Version list


class Distribution(Generic[DI]):
    info: DI
    path: Path
    platform: str

    info_raw: DI
    info_defaults: Optional[DI]
    platform_map: Optional[Dict[str, str]]
    dist_platform: str

    dist_name: Optional[str] = None
    strip_leading: Union[bool, str] = True
    fill_platform: ClassVar[bool] = False
    any_platform: ClassVar[bool] = False
    format_url: ClassVar[bool] = True
    default_binary_name: ClassVar[str]

    def __init__(self, info: DI, dist_path: Path, platform=None,
            platform_map: Optional[Dict[str, str]]=None,
            defaults: Optional[DI]=None):
        self.info_raw = info
        self.info_defaults = defaults
        self.platform_map = platform_map

        dist_platform = platform_map[platform] if platform_map and platform else platform
        if defaults is not None:
            info = ChainMap(info, defaults) # type:ignore

        if "platforms" in info:
            if dist_platform is None:
                dist_platform = info["platforms"][0]
            elif dist_platform not in info["platforms"]:
                raise ValueError(f"Incompatible platform set: {info['platforms']}; Running {dist_platform}")
        elif self.any_platform:
            platform = dist_platform = "any"
        elif dist_platform is not None and self.fill_platform:
            pass
        else:
            raise ValueError(f"Missing platforms key in distribution {info}")

        self.dist_platform = dist_platform
        self.platform = ({p:k for k,p in platform_map.items()} if platform_map else {}).get(dist_platform, platform)

        if self.dist_name is None:
            self.dist_name = dist_path.name
        if "strip_leading" in info:
            self.strip_leading = info["strip_leading"]

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
            url = self.info["url"].format(platform=self.platform, version=self.version_str)
        else:
            url = self.generate_url()
        self.__dict__["url"] = url
        return url

    def generate_url(self) -> str:
        raise NotImplementedError()

    def match(self, name: str) -> bool:
        return ("alias" in self.info and name in self.info["alias"]) or name == self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} {version_str(self.version)} '{self.name}' at 0x{id(self):x}>"

    @classmethod
    def load(cls: Type[D], infos: Sequence[DI], dist_path: Path, platform: Optional[str] = None) -> List[D]:
        return [cls(i, dist_path, platform)
                for i in infos
                if platform is None or "platforms" not in i or platform in i["platforms"]]

    @classmethod
    def load_v2(cls: Type[D], data: DistributionList, dist_path: Path, platform: Optional[str] = None) -> List[D]:
        if data["name"] != dist_path.name:
            raise ValueError(f"Distribution name mismatch: {dist_path} <=> {data['name']}")
        platform_map = None
        if "platforms" in data:
            if platform is not None:
                if platform not in data["platforms"]:
                    return []
            if isinstance(data["platforms"], dict):
                platform_map = data["platforms"]
            elif isinstance(data["platforms"], list):
                platform_map = {p:p for p in data["platforms"]}
            else:
                raise ValueError(f"Unsupported value for DistributionList::platforms: {type(data['platforms'])}. Expected dict or list.")
        if platform is not None:
            dist_platform = platform_map[platform] if platform_map else platform
        default = data["default"] if "default" in data else None
        return [cls(i, dist_path, platform, platform_map, default)
                for i in data["versions"]
                if platform is None or "platforms" not in i or dist_platform in i["platforms"]]

    @classmethod
    def load_json(cls: Type[D], filename: Path, dist_path: Path, platform: Optional[str] = None, *, v2: bool=False) -> List[D]:
        load: Callable[[Any, Path, Optional[str]], List[D]] = cls.load_v2 if v2 else cls.load # type: ignore
        with open(filename, "r") as f:
            return load(json_load(f), dist_path, platform)
