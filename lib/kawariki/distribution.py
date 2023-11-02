from collections import ChainMap
from functools import cached_property
from json import load as json_load
from pathlib import Path
from string import Formatter
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, List, Literal, Optional,
                    Sequence, Tuple, Type, TypedDict, TypeVar, Union, overload)

from .misc import version_str
from .utils.interpolated_chain_map import PatternInterpolatedChainMap

T = TypeVar("T")
D = TypeVar("D", bound="Distribution")
DI = TypeVar("DI", bound="DistributionInfo")


class DistributionInfo(TypedDict, total=False):
    name: str               # Distribution name
    version: Sequence[int]  # Distribution version (required)
    platforms: Sequence[str]# Compatible platforms
    url: str                # Download URL (tar archive, required)
    binary: str             # Binary name
    alias: Sequence[str]    # Aliases for humans
    strip_leading: str|bool # Strip leading component from archive filename

class DistributionList(TypedDict, total=False): # Generic[DI], unsupported w/ TypedDict until 3.11
    format: Literal[2]                          # Format version
    name: str                                   # Required; Name of folder inside dist/
    platforms: Union[List[str], Dict[str, str]] # Bounding set of supported platforms with renames
    common: DistributionInfo                    # Default values for all versions
    versions: Sequence[DistributionInfo]        # Required; Version list


class DistributionFormatter(Formatter):
    def convert_field(self, value: Any, conversion: str) -> Any:
        if conversion == 'v':
            return version_str(value)
        return super().convert_field(value, conversion)


class DistributionInfoProperty(Generic[T]):
    key: str
    convert: Optional[Callable[[Any], T]]

    def __init__(self, key: str, convert: Optional[Callable[[Any], T]]=None):
        self.key = key
        self.convert = convert

    @overload
    def __get__(self, instance: None, owner=None) -> 'DistributionInfoProperty[T]': ...
    @overload
    def __get__(self, instance: object, owner=None) -> T: ...

    def __get__(self, instance, owner=None) -> Union[T, 'DistributionInfoProperty[T]']:
        if instance is None:
            return self
        value = instance.info[self.key]
        if self.convert is not None:
            value = self.convert(value)
        return value


class Distribution(Generic[DI]):
    info: DI
    path: Path
    host_platform: str

    raw: DI
    common: Dict[str, Any]
    computed: Dict[str, str]
    platform_map: Optional[Dict[str, str]]

    defaults = {
        "slug": "{dist_name}-{version!v}-{platform}",
        "name": "{dist_name} {version!v} ({platform})",
        "alias": [],
        "strip_leading": True,
    }

    formatter = DistributionFormatter()

    def __init__(self, info: DI, dist_path: Path, platform=None,
            platform_map: Optional[Dict[str, str]]=None,
            common: DI={}):
        self.path = dist_path
        self.platform_map = platform_map

        self.raw = info
        self.common = common
        self.computed = computed = {
            "dist_name": dist_path.name,
            "dist_path": dist_path,
            "platform_host": platform,
        }

        self.info = infos = PatternInterpolatedChainMap(computed, info, common, self.defaults, formatter=self.formatter)

        # Compute distribution platform name
        dist_platform = platform_map[platform] if platform_map and platform else platform
        if platforms := infos.get('platforms'):
            if dist_platform is None:
                dist_platform = platforms[0]
            elif dist_platform not in platforms:
                if "any" in platforms:
                    dist_platform = "any"
                else:
                    raise ValueError(f"Incompatible platform set: {platforms}; Running {dist_platform}")
        else:
            raise ValueError(f"Missing platforms key in distribution {info}")

        computed["platform"] = dist_platform
        computed["platform_name"] = ({p:k for k,p in platform_map.items()} if platform_map else {}).get(dist_platform, platform)

        self.path = dist_path / self.slug
    
    version = DistributionInfoProperty[Tuple[int|str, ...]]("version", tuple)
    version_str = DistributionInfoProperty[str]("version", version_str)
    slug = DistributionInfoProperty[str]("slug")
    name = DistributionInfoProperty[str]("name")
    url = DistributionInfoProperty[str]("url")
    platform = DistributionInfoProperty[str]("platform_name")
    dist_platform = DistributionInfoProperty[str]("platform")
    strip_leading = DistributionInfoProperty[str|bool]("strip_leading")
    aliases = DistributionInfoProperty[List[str]]("alias")

    def match(self, alias: str) -> bool:
        return alias == self.slug or alias in self.aliases

    @property
    def available(self) -> bool:
        return self.path.exists()

    @property
    def binary(self) -> Path:
        return self.path / self.info["binary"]

    def __repr__(self):
        return f"<{self.__class__.__name__} {version_str(self.version)} '{self.slug}' at 0x{id(self):x}>"

    @classmethod
    def load_variants(cls: Type[D], info: DI, dist_path: Path, platform=None,
            platform_map: Optional[Dict[str, str]]=None,
            defaults: Optional[DI]=None) -> Iterable[D]:
        return (cls(info, dist_path, platform, platform_map, defaults),)

    @classmethod
    def load_v2(cls: Type[D], data: DistributionList, dist_path: Path, platform: Optional[str] = None) -> List[D]:
        if data["name"] != dist_path.name:
            raise ValueError(f"Distribution name mismatch: {dist_path} <=> {data['name']}")
        platform_map = None
        if "platforms" in data:
            if platform is not None:
                if platform not in data["platforms"]:
                    print(f"Warning: Current platform {platform} not included in supported platforms of distribution {data['name']}: {data['platforms']}")
                    return []
            if isinstance(data["platforms"], dict):
                platform_map = data["platforms"]
            elif isinstance(data["platforms"], list):
                platform_map = {p:p for p in data["platforms"]}
            else:
                raise ValueError(f"Unsupported value for DistributionList::platforms: {type(data['platforms'])}. Expected dict or list.")
        if platform is not None:
            dist_platform = platform_map[platform] if platform_map else platform
        common = data.get("common", {})
        return [ver
                for i in data["versions"]
                if platform is None or "platforms" not in i or dist_platform in i["platforms"]
                for ver in cls.load_variants(i, dist_path, platform, platform_map, common)]

    @classmethod
    def load_json(cls: Type[D], filename: Path, dist_path: Path, platform: Optional[str] = None, *, v2: bool=False) -> List[D]:
        with open(filename, "r") as f:
            data = json_load(f)
            if isinstance(data, dict):
                if data.get('format', 2) != 2:
                    raise ValueError(f"Unknown format version in versions.json file: {filename}")
                return cls.load_v2(data, dist_path, platform)
            else:
                raise ValueError(f"Old versions.json format: {filename}")
