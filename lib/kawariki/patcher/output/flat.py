# :---------------------------------------------------------------------------:
#   Store patched files normally
# :---------------------------------------------------------------------------:

from ..common import APatcherOut

import os.path
import pathlib
import shutil


class PatcherToCopy(APatcherOut):
    def __init__(self, path: pathlib.Path, copy_function=shutil.copy2):
        self.path = path
        self.copy_function = copy_function
    
    def add_file(self, dstname, src):
        dstpath = self.path / dstname
        if not dstpath.exists() or not os.path.samefile(dstpath, src):
            dstpath.parent.mkdir(parents=True, exist_ok=True)
            self.copy_function(src, dstpath)
    
    def write_file(self, dstname, content, mode=0o644):
        dstpath = self.path / dstname
        if dstpath.exists():
            os.unlink(dstpath)
        else:
            dstpath.parent.mkdir(parents=True, exist_ok=True)
        with open(dstpath, "xb") as f:
            f.write(content)
        os.chmod(dstpath, mode)

class PatcherInPlace(PatcherToCopy):
    def skip_file(self, dstname: str):
        os.unlink(self.path / dstname)
