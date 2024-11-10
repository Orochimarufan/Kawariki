from collections.abc import Iterator
from os import DirEntry, scandir
from typing import IO

from ..utils.typing import override
from . import AnyPath, FileModeRO, Fs, OsPath, Path


class OsEntry:
    __slots__ = ("parent", "de")

    def __init__(self, parent: Path, de: DirEntry):
        self.parent = parent
        self.de = de

    @property
    def name(self) -> str:
        return self.de.name

    @property
    def path(self) -> Path:
        return self.parent / self.de.name

    def is_dir(self) -> bool:
        return self.de.is_dir()

    def is_file(self) -> bool:
        return self.de.is_file()


class OsFs(Fs):
    def __init__(self, root: AnyPath):
        self.os_root = OsPath(root).resolve()

    @override
    def close(self):
        pass

    @property
    @override
    def reference(self):
        return f"os:{self.os_root}"

    @override
    def get_os_path(self, path: AnyPath) -> OsPath:
        path = OsPath(path)
        if path.is_absolute():
            path = path.relative_to("/")
        return self.os_root / path

    @override
    def exists(self, path: AnyPath) -> bool:
        return self.get_os_path(path).exists()

    @override
    def is_dir(self, path: AnyPath) -> bool:
        return self.get_os_path(path).is_dir()

    @override
    def is_file(self, path: AnyPath) -> bool:
        return self.get_os_path(path).is_file()

    @override
    def scandir(self, path) -> Iterator[OsEntry]:
        root = Path(self, path)
        for de in scandir(self.get_os_path(path)):
            yield OsEntry(root, de)

    @override
    def open(self, path: AnyPath, mode: FileModeRO, *, encoding=None, errors=None) -> IO[str] | IO[bytes]:
        return self.get_os_path(path).open(mode, encoding=encoding, errors=errors)
