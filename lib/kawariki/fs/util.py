
from shutil import copyfileobj

from . import Path, OsPath

__all__ = ["copy_from"]

def copy_from(src: Path, dst: OsPath):
    if dst.is_dir():
        dst /= src.name
    with src.open('rb') as f:
        with dst.open('wb') as fd:
            copyfileobj(f, fd)
