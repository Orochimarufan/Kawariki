# :---------------------------------------------------------------------------:
#   Misc. utilities
# :---------------------------------------------------------------------------:

from errno import EXDEV
from os import link, unlink
from os.path import exists
from shlex import join as shlex_join
from shutil import copy2
from textwrap import dedent
from typing import Generic, TypeVar, Union, overload

T = TypeVar("T")


def version_str(ver: tuple):
    return '.'.join(map(str, ver))


def copy_unlink(src, dst):
    # Unlink first to be able to overwrite write-protected files
    if exists(dst):
        unlink(dst)
    return copy2(src, dst)

def hardlink_or_copy(src, dst):
    try:
        link(src, dst)
    except OSError as e:
        if e.errno != EXDEV:
            raise
    else:
        return
    copy2(src, dst)


def format_launcher_script(*args, append_args=True):
        return dedent(f'''\
            #!/bin/sh
            cd "`dirname "$0"`"
            exec {shlex_join(map(str, args))}{' "$@"' if append_args else ""}
            ''')


class ErrorCode(Exception):
    code: int
    def __init__(self, code: int):
        super().__init__()
        self.code = code

