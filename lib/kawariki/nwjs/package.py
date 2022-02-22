
from json import load as json_load
from pathlib import Path
from typing import Any, Dict, Optional
from zipfile import ZipFile, is_zipfile

from ..fs import Fs


class PackageNw:
    def __init__(self, path: Path, json: str, is_archive: bool, *, may_clobber: bool=False):
        self.path = path
        self.json = json
        self.is_archive = is_archive
        self.may_clobber = may_clobber

    @property
    def package_json(self) -> Path:
        return self.path / self.json

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
        return PackageNw(target, self.json, False, may_clobber=as_temp)

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
