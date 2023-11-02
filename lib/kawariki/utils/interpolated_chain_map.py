
from string import Formatter
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar
from functools import cached_property
from fnmatch import fnmatchcase
from re import compile as re_compile

T = TypeVar("T")


class InterpolationError(LookupError):
    pass


class InterpolatedChainMap(Generic[T]):
    """ Read-only chain map with lazy (recursive) string interpolation """
    _maps: List[Dict[str, T]]
    _cache: Dict[str, T]
    _formatter: Optional[Formatter]

    def __init__(self, *maps: Dict[str, T], formatter: Optional[Formatter]=None):
        self._maps = list(maps)
        self._cache = {}
        self._formatter = formatter

    @cached_property
    def _keys(self) -> Set[str]:
        return set().union(*self._maps)
    
    def _invalidate(self):
        self._cache.clear()
        del self._keys

    def prepend(self, map: Dict[str, T]):
        self._maps.insert(0, map)
        self._invalidate()

    def _getraw(self, key: str) -> T:
        for mapping in self._maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        raise KeyError(key)

    def _interpolate(self, key: str, val: T) -> T:
        if isinstance(val, str):
            try:
                return self._formatter.vformat(val, (), self) \
                    if self._formatter else val.format_map(self)
            except KeyError as e:
                raise InterpolationError(key, f"Missing interpolated key '{e.args[0]}'")
            except ValueError as e:
                raise InterpolationError(key, *e.args)
        elif isinstance(val, list):
            return [self._interpolate(key, v) for v in val]
        return val

    def __getitem__(self, key: str) -> T:
        try:
            return self._cache[key]
        except KeyError:
            pass
        value = self._getraw(key)
        value = self._interpolate(key, value)
        self._cache[key] = value
        return value

    def get(self, key: str, default=None) -> T:
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self) -> int:
        return len(self._keys)     # reuses stored hash values if possible
    
    def keys(self) -> List[str]:
        return list(self._keys)

    def __iter__(self):
        return iter(self._keys)

    def __contains__(self, key):
        return key in self._keys

    def __bool__(self):
        return any(self.maps)


class PatternInterpolatedChainMap(InterpolatedChainMap[T]):
    def _interpolate(self, key: str, val: T) -> T:
        if isinstance(val, dict):
            for pattern, newval in val.items():
                if all(self._match_pattern(key, part) for part in pattern.split(';')):
                    return self._interpolate(key, newval)
            raise KeyError(key, f"No matching pattern interpolation: {'|'.join(val.keys())}", self._cache)
        else:
            return super()._interpolate(key, val)

    _PATTERN_RE = re_compile(r"^(?:(?P<not>!)?(?P<truth>[^=]+?)|(?P<key>.+?)(?P<op>!?=)(?P<pattern>.+))$")

    def _match_pattern(self, key, pattern: str) -> bool:
        if not pattern:
            return True
        m = self._PATTERN_RE.match(pattern)
        if not m:
            raise ValueError(f"Invalid interpolation pattern {pattern} in key {key}")
        if ikey := m.group("truth"):
            op = "truth"
        else:
            op = m.group("op")
            ikey = m.group("key")
        try:
            value = self[ikey]
        except KeyError:
            return False
        if op == "truth":
            return bool(value) ^ (m.group("not") is not None)
        elif op in ("=", "!="):
            if isinstance(value, bool):
                res = m.group("pattern").lower() == str(value).lower()
            else:
                res = fnmatchcase(str(value), m.group("pattern"))
            return res ^ (op == "!=")
        raise RuntimeError("Pattern match error")
