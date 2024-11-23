from collections.abc import Generator
from contextlib import contextmanager
from enum import IntFlag, IntEnum
from functools import cached_property
from struct import Struct
from typing import IO
from os import SEEK_CUR, SEEK_END

from ..utils.typing import Self


PCK_MAGIC = b'GDPC'

class PckVersion(IntEnum):
    Godot3 = 1
    Godot4 = 2


class PckFlags(IntFlag):
    Defaults = 0
    Encrypted = 1 << 0


class PckEntryFlags(IntFlag):
    Defaults = 0
    Encrypted = 1 << 0


class PackReader:
    # === Helpers ===
    @staticmethod
    def find_offset(file: IO[bytes]) -> int:
        """ Find and return PCK start offset. Leave file cursor after magic. File should be at beginning """
        if file.read(4) == PCK_MAGIC:
            return 0
        # Try from the end
        file.seek(-4, SEEK_END)
        if file.read(4) == PCK_MAGIC:
            file.seek(-12, SEEK_CUR)
            ds = int.from_bytes(file.read(8), byteorder="little", signed=False)
            file.seek(-ds - 8, SEEK_CUR)
            offset = file.tell()
            if file.read(4) == PCK_MAGIC:
                return offset
        # Not valid
        raise ValueError(f"Not a valid Godot PCK file: {file.name}")

    HEADER_STRUCT_VERSION = Struct('<IIII') # not including magic
    HEADER_STRUCT_V4 = Struct('<IQ')
    ENTRY_STRUCT_COMMON = Struct('<QQ16s') # not including name

    def _read_struct(self, struct: Struct):
        return struct.unpack(self.file.read(struct.size))

    def _read_unsigned(self, size: int=4) -> int:
        return int.from_bytes(self.file.read(size), "little", signed=False)

    # === Constructors ===
    def __init__(self, file: IO[bytes]):
        self.file = file
        self.offset = self.find_offset(file)
        version, *self.engine_version = self._read_struct(self.HEADER_STRUCT_VERSION)
        if version == PckVersion.Godot3:
            self.version = PckVersion.Godot3
            self.flags = PckFlags.Defaults
        elif version == PckVersion.Godot4:
            self.version = PckVersion.Godot4
            flags, base = self._read_struct(self.HEADER_STRUCT_V4)
            self.flags = PckFlags(flags)
        else:
            raise NotImplementedError(f"Godot PCK version not supported: {version}")
        self.file.seek(16 * 4, SEEK_CUR)
        self.count = self._read_unsigned(4)

    @classmethod
    @contextmanager
    def open(cls, path) -> Generator[Self]:
        with open(path, 'rb') as f:
            yield cls(f)

    # === Data ===
    file: IO[bytes]
    offset: int
    version: PckVersion
    flags: PckFlags
    count: int
    engine_version: tuple[int, int, int]

    @property
    def is_encrypted(self) -> bool:
        return bool(self.flags & PckFlags.Encrypted)

    class Entry:
        reader: 'PackReader'
        name: str
        offset: int
        size: int
        md5: bytes
        flags: PckEntryFlags

        def __init__(self, reader: 'PackReader', name: str, offset: int, size: int, md5: bytes, flags: PckEntryFlags):
            self.reader = reader
            self.name = name
            self.offset = offset
            self.size = size
            self.md5 = md5
            self.flags = flags

        @property
        def is_encrypted(self) -> bool:
            return bool(self.flags & PckEntryFlags.Encrypted)

    @cached_property
    def entries(self) -> dict[str, Entry]:
        if self.is_encrypted:
            raise NotImplementedError("PCK with encrypted index not currently supported")
        entries = {}
        for i in range(self.count):
            name_length = self._read_unsigned(4)
            name = self.file.read(name_length).rstrip(b'\0').decode('utf-8')
            offset, size, md5 = self._read_struct(self.ENTRY_STRUCT_COMMON)
            flags = PckEntryFlags(self._read_unsigned(4)) if self.version == PckVersion.Godot4 else \
                    PckEntryFlags.Defaults
            entry = self.Entry(self, name, offset, size, md5, flags)
            # TODO: handle duplicates
            entries[name] = entry
        return entries
