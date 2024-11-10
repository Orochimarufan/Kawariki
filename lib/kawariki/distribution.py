from collections.abc import Callable, Iterable, Sequence
from json import load as json_load
from pathlib import Path
from string import Formatter
from typing import Any, ClassVar, Generic, Literal, TypedDict, TypeVar, cast, overload

from .misc import version_str
from .utils.typing import Self
from .utils.interpolated_chain_map import PatternInterpolatedChainMap

T = TypeVar("T")


class DistributionInfo(TypedDict, total=False):
    """ Common items in distribution info JSON objects """
    name: str                       # Distribution name
    slug: str                       # Slug for folder names
    version: Sequence[int]          # Distribution version (required)
    platforms: Sequence[str]        # Compatible platforms
    url: str                        # Download URL (tar archive, required)
    binary: str                     # Binary name
    alias: Sequence[str]            # Aliases for humans
    strip_leading: str|bool         # Strip leading component from archive filename


class DistributionList(TypedDict, total=False): # Generic[DI], unsupported w/ TypedDict until 3.11
    """ Root object of versions.json files """
    format: Literal[2]                          # Format version
    name: str                                   # Required; Name of folder inside dist/
    platforms: list[str]|dict[str, str]         # Bounding set of supported platforms with renames
    common: DistributionInfo                    # Default values for all versions
    versions: Sequence[DistributionInfo]        # Required; Version list


class DistributionFormatter(Formatter):
    """ String formatter with additional conversions:
        - !v: Format a version tuple by converting elements to str and joining by .
    """
    def convert_field(self, value: Any, conversion: str|None) -> Any:
        if conversion == 'v':
            return version_str(value)
        return super().convert_field(value, conversion)


class DistributionInfoProperty(Generic[T]):
    """ Property extracting a key from the .info attribute """
    key: str
    convert: Callable[[Any], T]|None

    def __init__(self, key: str, convert: Callable[[Any], T]|None=None):
        self.key = key
        self.convert = convert

    @overload
    def __get__(self, instance: None, owner=None) -> 'DistributionInfoProperty[T]': ...
    @overload
    def __get__(self, instance: object, owner=None) -> T: ...

    def __get__(self, instance, owner=None) -> T|'DistributionInfoProperty[T]':
        if instance is None:
            return self
        value = instance.info[self.key]
        if self.convert is not None:
            value = self.convert(value)
        return value


class DistributionInfoPropertyOptional(DistributionInfoProperty[T]):
    @overload
    def __get__(self, instance: None, owner=None) -> 'DistributionInfoPropertyOptional[T]': ...
    @overload
    def __get__(self, instance: object, owner=None) -> T: ...

    def __get__(self, instance, owner=None) -> T|'DistributionInfoPropertyOptional[T]'|None:
        if instance is None:
            return self
        value = instance.info.get(self.key)
        if value is not None and self.convert is not None:
            value = self.convert(value)
        return value


DI = TypeVar("DI", bound=DistributionInfo)

class Distribution(Generic[DI]):
    """ Represents a specific distribution of a component
        A wrapper around a DistributionInfo dict
    """
    info: DI
    path: Path
    host_platform: str

    raw: DI
    common: DI
    computed: dict[str, str]
    platform_map: dict[str, str]|None

    defaults: ClassVar[DistributionInfo] = {
        "slug": "{dist_name}-{version!v}-{platform}",
        "name": "{dist_name} {version!v} ({platform})",
        "alias": [],
        "strip_leading": True,
    }

    formatter = DistributionFormatter()

    def __init__(self, info: DI, dist_path: Path, platform=None,
                 platform_map: dict[str, str]|None=None,
                 common: DI|None=None):
        self.path = dist_path
        self.platform_map = platform_map

        self.raw = info
        self.common = common or cast(DI, {})
        self.computed = computed = {
            "dist_name": dist_path.name,
            "dist_path": dist_path,
            "platform_host": platform,
        }

        # type: ignore
        self.info = infos = PatternInterpolatedChainMap( # type: ignore[assignment] # ChainMap is compatible
            computed, info, common, self.defaults, # type: ignore[arg-type] # TypedDicts are also dicts
            formatter=self.formatter)

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
        computed["platform_name"] = (({p: k for k, p in platform_map.items()}).get(dist_platform, platform)
                                     if platform_map else platform)

        self.path = dist_path / self.slug

    # Attributes
    version = DistributionInfoProperty[tuple[int|str, ...]]("version", tuple)
    version_str = DistributionInfoProperty[str]("version", version_str)
    slug = DistributionInfoProperty[str]("slug")
    name = DistributionInfoProperty[str]("name")
    url = DistributionInfoProperty[str]("url")
    platform = DistributionInfoProperty[str]("platform_name")
    dist_platform = DistributionInfoProperty[str]("platform")
    strip_leading = DistributionInfoProperty[str|bool]("strip_leading")
    aliases = DistributionInfoProperty[list[str]]("alias")

    @property
    def available(self) -> bool:
        """ Whether distribution is avaliable locally """
        return self.path.exists()

    @property
    def binary(self) -> Path:
        """ Path to the main binary file """
        return self.path / self.info["binary"]

    # Methods
    def match(self, alias: str) -> bool:
        """ Check if this distribution matches an alias name """
        return alias == self.slug or alias in self.aliases

    def __repr__(self):
        return f"<{self.__class__.__name__} {version_str(self.version)} '{self.slug}' at 0x{id(self):x}>"

    # Loading from JSON
    @classmethod
    def load_variants(cls, info: DI, dist_path: Path, platform=None,
                      platform_map: dict[str, str]|None=None,
                      defaults: DI|None=None) -> Iterable[Self]:
        """ Allow subclass to synthesize multiple variants from one versions.json entry """
        return (cls(info, dist_path, platform, platform_map, defaults),)

    @classmethod
    def load_data(cls, data: DistributionList, dist_path: Path, platform: str|None = None) -> list[Self]:
        """ Load all distributions from JSON object """
        if data["name"] != dist_path.name:
            raise ValueError(f"Distribution name mismatch: {dist_path} <=> {data['name']}")
        platform_map = None
        if "platforms" in data:
            if platform is not None and platform not in data["platforms"]:
                print(f"Warning: Current platform {platform} not included in supported platforms "
                      f"of distribution {data['name']}: {data['platforms']}")
                return []
            if isinstance(data["platforms"], dict):
                platform_map = data["platforms"]
            elif isinstance(data["platforms"], list):
                platform_map = {p: p for p in data["platforms"]}
            else:
                raise ValueError(f"Unsupported value for /platforms: {type(data['platforms'])}. Expected dict or list.")
        dist_platform = platform_map[platform] if platform_map and platform else platform
        common = data.get("common", {})
        return [ver
                for i in data["versions"]
                if platform is None or "platforms" not in i or dist_platform in i["platforms"]
                for ver in cls.load_variants(i, dist_path, platform, platform_map, common)]

    @classmethod
    def load_json(cls, filename: Path, dist_path: Path, platform: str|None = None) -> list[Self]:
        """ Load distributions from versions.json file """
        with open(filename, "r", encoding="utf8") as f:
            data = json_load(f)
            if isinstance(data, dict):
                if data.get('format', 2) != 2:
                    raise ValueError(f"Unknown format version in versions.json file: {filename}")
                return cls.load_data(data, dist_path, platform)  # type: ignore
            raise ValueError(f"Old versions.json format: {filename}")
