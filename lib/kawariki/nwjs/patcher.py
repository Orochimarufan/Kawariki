# :---------------------------------------------------------------------------:
#   Patch game install
# :---------------------------------------------------------------------------:

from ..patcher.common import APatcher, APatcherOut
from .runtime import Runtime, NWjs

import pathlib
import os


class Patcher(APatcher):
    def __init__(self, nwjs: NWjs):
        self.nwjs = nwjs

    @classmethod
    def exclude_filter(cls, path: pathlib.PurePath):
        return (path.parent.name in ("swiftshader", "locales")
                or  path.name in ("nw_100_percent.pak", "nw_200_percent.pak", "resources.pak",
                                "natives_blob.bin", "snapshot_blob.bin", "v8_context_snapshot.bin", "icudtl.dat")
                or  path.suffix in (".dll", ".exe", ".lib", ".node"))
    
    @classmethod
    def patch_filter(cls, path: pathlib.PurePath):
        return path.name in ("greenworks.js",)

    def add_patched(self, dst: APatcherOut, patches):
        for rpath in patches:
            if rpath.name == "greenworks.js":
                self.add_greenworks(dst, rpath)
            else:
                raise ValueError(f"No patch available for {rpath}")
    
    def add_greenworks(self, dst: APatcherOut, rpath):
        if not self.nwjs.has("greenworks"):
            raise ValueError(f"Selected NW.js {self.nwjs.dist} doesn't have Greenworks support")
        gw_path = self.nwjs.get_path("greenworks")
        for root, _, files in os.walk(gw_path):
            rootpath = pathlib.Path(root)
            self.add_files_from_list(dst, rpath.parent / rootpath.relative_to(gw_path), root, files)
    
    def add_runtime(self, dst: APatcherOut):
        nw_path = self.nwjs.get_path("dist")
        for root, _, files in os.walk(nw_path):
            rootpath = pathlib.Path(root)
            self.add_files_from_list(dst, rootpath.relative_to(nw_path.parent), rootpath, files)
    
    def get_launch_argv(self, game):
        return f"{self.nwjs.dist}/nw", game.package_dir
