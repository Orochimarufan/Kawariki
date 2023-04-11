
from json import load as json_load
from pathlib import Path
from typing import Any, Dict, Optional
from zipfile import ZipFile, is_zipfile

from ..fs import Fs


class PackageNw:
    """
    Represents a NW.js application package

    A package may be a directory of loose files or an archive.

    Attributes:
        path - The path of the directory or archive file
        json - The filename of the package manifest (usually package.json)
        is_archive - Whether it is an archive file (as opposed to directory of loose files)
        may_clobber - Whether this refers to a copy (e.g. from unpacking an archive) and
                    will be discarded later, making it safe to modify files directly
        original - A PackageNw instance this one was copied (or extracted) from
    """
    path: Path
    json: str
    is_archive: bool
    may_clobber: bool
    original: Optional["PackageNw"]

    def __init__(self, path: Path, json: str, is_archive: bool, *,
                may_clobber: bool=False, original: Optional["PackageNw"]=None):
        self.path = path
        self.json = json
        self.is_archive = is_archive
        self.may_clobber = may_clobber
        self.original = original

    @property
    def package_json(self) -> Path:
        """ The full path to the package.json file
        Note: may include path components inside an archive
        """
        return self.path / self.json

    @property
    def enclosing_directory(self) -> Path:
        """ An approximation of the "enclosing directory":
        - the original "enclosing directory" if this is a copy
        - the containing directory if it is an archive
        - the parent directory if the package root is called "package.nw"
        - the package root directory otherwise

        This is intended for looking up user-generated files relative to
        a game directory (e.g. configs, userscripts).

        Generally, it should result in the directory containing the shipped
        NW.js binaries and either package.json or package.nw (dir or archive)
        """
        if self.original is not None:
            return self.original.enclosing_directory
        elif self.is_archive or self.path.name == "package.nw":
            return self.path.parent
        else:
            return self.path

    # For reading
    def open_fs(self) -> Fs:
        if not self.is_archive:
            from ..fs.os import OsFs
            return OsFs(self.path)
        else:
            from ..fs.zip import ZipFs
            return ZipFs(self.path)

    def read_json(self) -> Dict[str, Any]:
        with self.open_fs() as fs:
            with fs.open(self.json, "r") as f:
                return json_load(f)

    # Unpack into directory
    def unarchive(self, target: Path, *, as_temp: bool=False) -> 'PackageNw':
        if not isinstance(target, Path):
            target = Path(target)
        if not self.is_archive:
            raise ValueError("Package isn't archived")
        if not target.exists():
            target.mkdir(parents=True)
        with ZipFile(self.path, "r") as zf:
            zf.extractall(target)
        return PackageNw(target, self.json, False, may_clobber=as_temp, original=self)

    # Find the NW package, if any, in a directory
    @classmethod
    def find(cls, root: Path, binary_name_hint: Optional[str]=None) -> Optional['PackageNw']:
        # Plain
        if (pkg := root / "package.json").exists():
            return cls(root, "package.json", False)
        # package.nw archive
        if (pkg := root / "package.nw").exists():
            return cls(pkg, "package.json", pkg.is_file())
        # Archive appended to executable
        if (binary_name_hint is not None
                and (pkg := root / binary_name_hint).exists()
                and is_zipfile(pkg)):
            # XXX: Should probably check if it actually contains a package.json
            return cls(pkg, "package.json", True)
        # RPGMaker MV
        if (p := root / "www" / "package.json").exists():
            return cls(p.parent, "package.json", False)
        # Last-ditch effort XXX: remove this?
        for p in root.rglob("package.json"):
            print(f"Using non-standard package.json location {p}")
            return cls(p.parent, "package.json", False)
        return None
