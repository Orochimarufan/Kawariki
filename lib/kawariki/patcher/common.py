
import os
from abc import abstractmethod
from pathlib import Path, PurePath
from typing import Sequence

from ..game import Game
from ..misc import format_launcher_script


class APatcherOut:
    def __enter__(self):
        return self

    @abstractmethod
    def add_file(self, dstname: str, src: Path):
        pass

    @abstractmethod
    def write_file(self, dstname: str, content: bytes, mode: int):
        pass

    def skip_file(self, dstname: str):
        pass

    def __exit__(self, t, e, tb):
        pass


class APatcher:
    # For use in subclasses
    def add_file(self, dst: APatcherOut, dstname, srcpath: Path):
        print(f"Adding file   '{dstname}'")
        dst.add_file(dstname, srcpath)

    def skip_file(self, dst: APatcherOut, dstname):
        print(f"Skipping file '{dstname}'")
        dst.skip_file(dstname)
    
    def add_files_from_list(self, dst: APatcherOut, dstpath: Path, srcpath: Path, flist: Sequence[str]):
        for fname in flist:
            self.add_file(dst, dstpath / fname, srcpath / fname)
    
    # Abstract
    @abstractmethod
    def exclude_filter(cls, path: PurePath):
        """ return True if file should be omitted in patched game """
    
    @abstractmethod
    def patch_filter(cls, path: PurePath):
        """ return True if file should be processed independently later """

    @abstractmethod
    def add_patched(self, dst: APatcherOut, patches: "list[Path]"):
        """ process files marked for patching """
    
    @abstractmethod
    def add_runtime(self, dst: APatcherOut):
        """ Add the new runtime files """
    
    @abstractmethod
    def get_launch_argv(self, game: Game):
        """ return command to run game in pached file structure """

    # Implementation methods
    def add_game_files(self, dst: APatcherOut, src: Path):
        patches = []
        for root, _, files in os.walk(src):
            proot = Path(root)
            rroot = proot.relative_to(src)
            for fname in files:
                rpath = rroot / fname
                if self.patch_filter(rpath):
                    patches.append(rpath)
                elif self.exclude_filter(rpath):
                    self.skip_file(dst, rpath)
                else:
                    self.add_file(dst, rpath, proot / fname)
                    
        return patches
    
    def add_launcher(self, dst: APatcherOut, game: Game):
        print("Adding launcher script 'Game.sh'")
        dst.write_file("Game.sh", format_launcher_script(*self.get_launch_argv(game)).encode("utf-8"), mode=0o755)

    # Public api
    def run(self, dst: APatcherOut, game: Game):
        with dst:
            patches = self.add_game_files(dst, game.root)
            self.add_patched(dst, patches)
            self.add_runtime(dst)
            self.add_launcher(dst, game)
