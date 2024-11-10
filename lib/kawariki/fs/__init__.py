# Filesystem Abstraction

from abc import ABC, abstractmethod
from collections.abc import Iterator
from os import PathLike, fspath
from pathlib import Path as OsPath
from pathlib import PurePath as PureNativePath
from pathlib import PurePosixPath
from typing import IO, Literal, Protocol, TypeVar, overload

from ..utils.typing import override

__all__ = ["AnyPath", "Entry", "Fs", "PurePath", "Path", "string_path"]


_Fs = TypeVar("_Fs", bound="Fs")
_Path = TypeVar("_Path", bound="Path")
_PurePath = TypeVar("_PurePath", bound="PurePath")

FileModeRO = Literal["r", "rb"]
AnyPath = str | PathLike[str]


def string_path(path: AnyPath) -> str:
    if isinstance(path, str):
        return path
    return fspath(path)


class Entry(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def path(self) -> 'Path': ...
    def is_dir(self) -> bool: ...
    def is_file(self) -> bool: ...


class Fs(ABC):
    # Resource management
    @abstractmethod
    def close(self): ...

    def __enter__(self: _Fs) -> _Fs:
        return self

    def __exit__(self, t, v, tb):
        self.close()

    # Fs Metadata
    @property
    def reference(self) -> str | None:
        return None

    @property
    def root(self) -> 'Path':
        return Path(self, '/')

    # File Metadata
    @abstractmethod
    def exists(self, path: AnyPath) -> bool: ...
    @abstractmethod
    def is_dir(self, path: AnyPath) -> bool: ...
    @abstractmethod
    def is_file(self, path: AnyPath) -> bool: ...

    # Branches
    @abstractmethod
    def scandir(self, path: AnyPath) -> Iterator[Entry]: ...

    # Leaves
    @overload
    def open(self, path: AnyPath, mode: Literal["r"], *, encoding=None, errors=None) -> IO[str]: ...
    @overload
    def open(self, path: AnyPath, mode: Literal["rb"]) -> IO[bytes]: ...
    @overload
    def open(self, path: AnyPath, mode: FileModeRO, *, encoding=None, errors=None) -> IO[str] | IO[bytes]: ...

    @abstractmethod
    def open(self, path: AnyPath, mode: FileModeRO, *, encoding=None, errors=None) -> IO[str] | IO[bytes]: ...

    def read_text(self, path: AnyPath, *, encoding=None, errors=None) -> str:
        with self.open(path, "r", encoding=encoding, errors=errors) as f:
            return f.read()

    def read_bytes(self, path: AnyPath) -> bytes:
        with self.open(path, "rb") as f:
            return f.read()

    def get_os_path(self, path: AnyPath) -> OsPath | None:
        return None


class PurePath(PurePosixPath):
    def __floordiv__(self: _PurePath, other: AnyPath) -> _PurePath:
        if isinstance(other, PurePath):
            return self / other.as_relative()
        if not isinstance(other, PureNativePath):
            other = PureNativePath(other)
        if other.is_absolute():
            other = other.relative_to(other.root)
        return self / other

    def as_relative(self) -> 'PurePath':
        if self.is_absolute():
            return PurePath(*self.parts[1:])
        return self


class Path(PurePath):
    def __init__(self, fs: Fs, *pathsegments: AnyPath):
        # Always absolute
        super().__init__("/", *pathsegments) # type: ignore
        self.fs = fs

    def with_segments(self, *pathsegments: AnyPath) -> 'Path':
        return Path(self.fs, *pathsegments)

    # Relative
    @property
    def pure(self) -> PurePath:
        return PurePath(self)

    @property
    def os_path(self) -> OsPath | None:
        return self.fs.get_os_path(self)

    @override
    def as_relative(self) -> PurePath:
        return PurePath(*self.parts[1:])

    @override
    def relative_to(self, *other: AnyPath):
        raise ValueError(f"{__name__}.Path cannot be relative")

    def exists(self) -> bool:
        return self.fs.exists(self)

    def is_dir(self) -> bool:
        return self.fs.is_dir(self)

    def is_file(self) -> bool:
        return self.fs.is_file(self)

    def scandir(self) -> Iterator[Entry]:
        return self.fs.scandir(self)

    @overload
    def open(self, mode: Literal["r"]="r", *, encoding=None, errors=None) -> IO[str]: ...
    @overload
    def open(self, mode: Literal["rb"]) -> IO[bytes]: ...
    @overload
    def open(self, mode: FileModeRO, *, encoding=None, errors=None) -> IO[str] | IO[bytes]: ...

    def open(self, mode: FileModeRO="r", *, encoding=None, errors=None) -> IO[str] | IO[bytes]:
        return self.fs.open(self, mode, encoding=encoding, errors=errors)

    def read_text(self, **kwds) -> str:
        return self.fs.read_text(self, **kwds)

    def read_bytes(self) -> bytes:
        return self.fs.read_bytes(self)

