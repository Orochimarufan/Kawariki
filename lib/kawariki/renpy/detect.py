from functools import cached_property
from itertools import zip_longest
from pathlib import Path
from re import compile as re_compile
from typing import ClassVar, List, Optional, Sequence, Tuple, Union

from ..utils.typing import Self


class RenpyVersion:
    valid = False
    branch: str = ""
    nightly: bool = False
    official: bool = False
    version: str = "0"
    version_name: str = ""
    vc_version: int = 0

    KEYS: ClassVar[Sequence[str]] = "branch", "nightly", "official", "version", "version_name", "vc_version"
    RE_TUP = re_compile(r"version_tuple\s*=\s*\((\d+, \d+, \d+), vc_version\)")
    RE_NAM = re_compile(r"version_name\s*=\s*\"([^\"]+)\"")

    @staticmethod
    def _parse_pykv_line(line: str) -> Tuple[Optional[str], Union[str,int,bool]]:
        """ vc_version.py is a python module with only top-level variable assignments.
            Try to read it like a simple Key=Value file
        """
        # TODO: maybe use ast or something?
        line = line.strip()
        if line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if v[0] == 'u':
                return k, v[2:-1]
            if v[0] == "'" or v[0] == '"':
                return k, v[1:-1]
            if v == "False":
                return k, False
            if v == "True":
                return k,  True
            if v.isdigit():
                return k,  int(v)
            if v == "None":
                return k, None
        return None, None

    @classmethod
    def _guess_version_from_initpy(cls, initpy: Path) -> Tuple[Tuple[int, ...], str]:
        # 8.0 and 7.5 share the same python code and contain both version numbers
        # Try to figure it out from the included python library folder
        with initpy.open() as f:
            buf = f.read()
        tups: List[Sequence[int]] = []
        nams: List[str] = []
        for m in cls.RE_TUP.finditer(buf):
            tups.append(tuple(int(d.strip()) for d in m.group(1).split(',')))
        for m in cls.RE_NAM.finditer(buf):
            nams.append(m.group(1))
        if tups:
            is_py3 = (initpy.parent.parent / "lib" / "python3.9").exists()
            for t, n in zip_longest(tups, nams, fillvalue=""):
                if not t:
                    break
                if is_py3 == (t[0] >= 8):
                    return t, n
        return (), ""

    def __init__(self, vc_version: Path):
        if vc_version.suffix == ".py":
            with vc_version.open() as f:
                for line in f:
                    k, v = self._parse_pykv_line(line)
                    if k in self.KEYS:
                        setattr(self, k, v)
            # vc_version is only included as the last component of version in 8.1+
            if self.vc_version == 0:
                if self.version != "0":
                    self.vc_version = self.version_info[-1]
            elif self.version == "0" :
                # Previously version was embedded in __init__.py
                tup, self.version_name = self._guess_version_from_initpy(vc_version.with_name("__init__.py"))
                if tup:
                    self.version_info = (*tup, self.vc_version)
                    self.version = ".".join(map(str, self.version_info))
            self.valid = self.version != "0"
        else:
            raise NotImplementedError("Reading the Ren'Py version from compiled python files isn't currently supported")

    def __bool__(self) -> bool:
        return self.valid

    @cached_property
    def version_info(self) -> Sequence[int]:
        return tuple(int(s) for s in self.version.split('.'))

    @property
    def is_python3(self) -> bool:
        return self.version_info[0] >= 8

    @staticmethod
    def find_version_file(path: Path) -> Optional[Path]:
        vc_version = path / "renpy" / "vc_version"
        for ext in (".py", ".pyo", ".pyc"):
            candidate = vc_version.with_suffix(ext)
            if candidate.exists():
                return candidate
        return None

    @classmethod
    def find(cls, path: Path) -> Optional[Self]:
        if vc_version := cls.find_version_file(path):
            return cls(vc_version)
        return None

    def __repr__(self) -> str:
        if self.valid:
            return f"<{self.__class__.__name__} {self.version} '{self.version_name}'>"
        else:
            return f"<{self.__class__.__name__} INVALID>"
