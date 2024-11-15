from collections.abc import Iterator
from functools import cached_property
from io import TextIOWrapper
from logging import getLogger
from typing import IO, Literal, overload
from zipfile import ZipFile, ZipInfo

from ..utils.typing import override
from . import AnyPath, FileModeRO, Fs, Path, PurePath

logger = getLogger(__name__)


class ZipEntry:
    __slots__ = ("parent", "name", "subtree")

    def __init__(self, parent: Path, name: str, subtree: dict):
        self.parent = parent
        self.name = name
        self.subtree = subtree

    @property
    def info(self) -> ZipInfo | None:
        return self.subtree.get(None)

    @property
    def path(self) -> Path:
        return self.parent / self.name

    def is_dir(self) -> bool:
        children = self.subtree.keys() - {None}
        return len(children) > 0 or self.info is not None and self.info.is_dir()

    def is_file(self) -> bool:
        return self.info is not None and not self.info.is_dir()


class ZipFs(Fs):
    def __init__(self, path: AnyPath):
        self._path = path
        if isinstance(path, Path):
            self.zip = ZipFile(path.open("rb"), "r")
        else:
            self.zip = ZipFile(path, "r")

    @override
    def close(self):
        self.zip.close()

    @cached_property
    @override
    def reference(self):
        if isinstance(self._path, Path):
            ref = self._path.fs.reference
            if not ref:
                return None
            return f"zip:{{{ref}#{self._path}}}"
        else:
            return f"zip:{self._path}"

    @cached_property
    def tree(self) -> dict:
        tree: dict = {}
        for info in self.zip.infolist():
            path = PurePath(info.filename).as_relative()
            node = tree
            for part in path.parts:
                node = node.setdefault(part, {})
            if None in node:
                logger.warn("Duplicate entry %s in %s", info.filename, self.reference)
                # Never overwrite a file with a dir entry
                if info.is_dir():
                    continue
            node[None] = info
        return tree

    def subtree(self, path: AnyPath) -> dict:
        node = self.tree
        for part in PurePath(path).as_relative().parts:
            node = node.get(part, {})
        return node

    def get_info(self, path: AnyPath) -> ZipInfo | None:
        return self.subtree(path).get(None)

    @override
    def exists(self, path: AnyPath) -> bool:
        return len(self.subtree(path)) > 0

    @override
    def is_dir(self, path: AnyPath) -> bool:
        tree = self.subtree(path)
        children = tree.keys() - {None}
        info: ZipInfo | None = tree.get(None)
        return len(children) > 0 or (info is not None and info.is_dir())

    @override
    def is_file(self, path: AnyPath) -> bool:
        info = self.get_info(path)
        return info is not None and not info.is_dir()

    @override
    def scandir(self, path: AnyPath) -> Iterator[ZipEntry]:
        root = Path(self, path)
        tree = self.subtree(path)
        for name, sub in tree.items():
            if name is None:
                continue
            yield ZipEntry(root, name, sub)

    @overload
    def open(self, path: AnyPath, mode: Literal["r"], *, encoding=None, errors=None) -> IO[str]: ...
    @overload
    def open(self, path: AnyPath, mode: Literal["rb"]) -> IO[bytes]: ...
    @overload
    def open(self, path: AnyPath, mode: FileModeRO, *, encoding=None, errors=None) -> IO[str] | IO[bytes]: ...

    @override
    def open(self, path: AnyPath, mode: FileModeRO, *, encoding=None, errors=None) -> IO[str] | IO[bytes]:
        info = self.get_info(path)
        if not info:
            raise FileNotFoundError(path)
        f = self.zip.open(info, "r")
        if mode == "rb":
            return f
        return TextIOWrapper(f, encoding, errors)
