# :---------------------------------------------------------------------------:
#   Save patched files to Tar archive
# :---------------------------------------------------------------------------:

from io import BytesIO
from pathlib import Path
from tarfile import TarFile, TarInfo
from tarfile import open as taropen
from typing import Optional

from ..common import APatcherOut


class PatcherToTar(APatcherOut):
    tar: Optional[TarFile]
    def __init__(self, path: Path):
        if path.suffix in (".gz", ".bz2", ".xz"):
            self._mode = f"x:{path.suffix[1:]}"
            if path.suffixes[-2] != ".tar":
                raise ValueError(f"Only tar archive output supported, not {path.suffixes[-2]}")
        elif path.suffix in (".tgz", ".tbz2", ".txz"):
            self._mode = f"x:{path.suffix[2:]}"
        elif path.suffix == ".tar":
            self._mode = "x"
        else:
            raise ValueError(f"Only tar archive output supported, not {path.suffix}")
        self.path = path
        self.tar = None
    
    def __enter__(self):
        self.tar = taropen(self.path, self._mode).__enter__()
        return self
    
    def add_file(self, dstname, src):
        assert self.tar is not None
        self.tar.add(src, dstname, False)
    
    def write_file(self, dstname, content: bytes, mode=0o644):
        i = TarInfo(name=dstname)
        i.size = len(content)
        i.mode = mode
        assert self.tar is not None
        self.tar.addfile(i, BytesIO(content))
    
    def __exit__(self, t, e, tb):
        tar = self.tar
        self.tar = None
        return tar.__exit__(t, e, tb)
