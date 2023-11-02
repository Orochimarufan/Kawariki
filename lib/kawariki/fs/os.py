from os import DirEntry, scandir
from pathlib import Path as OsPath
from typing import Iterator, Union, IO

from . import AnyPath, Fs, Path, FileModeRO


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

    def close(self):
        pass

    @property
    def reference(self):
        return f"os:{self.os_root}"

    def os_path(self, path: AnyPath) -> OsPath:
        path = OsPath(path)
        if path.is_absolute():
            path = path.relative_to("/")
        return self.os_root / path

    def exists(self, path: AnyPath) -> bool:
        return self.os_path(path).exists()

    def is_dir(self, path: AnyPath) -> bool:
        return self.os_path(path).is_dir()

    def is_file(self, path: AnyPath) -> bool:
        return self.os_path(path).is_file()

    def scandir(self, path) -> Iterator[OsEntry]:
        root = Path(self, path)
        for de in scandir(self.os_path(path)):
            yield OsEntry(root, de)

    def open(self, path: AnyPath, mode: FileModeRO, *, encoding=None, errors=None) -> Union[IO[str], IO[bytes]]:
        return self.os_path(path).open(mode, encoding=encoding, errors=errors)
