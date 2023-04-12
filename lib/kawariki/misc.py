# :---------------------------------------------------------------------------:
#   Misc. utilities
# :---------------------------------------------------------------------------:

from errno import EXDEV
from os import link, unlink
from os.path import exists
from shlex import join as shlex_join
from shutil import copy2
from textwrap import dedent
from typing import Generic, Sequence, TypeVar, Union, overload

T = TypeVar("T")


def version_str(ver: Sequence[Union[str, int]]):
    return '.'.join(map(str, ver))

def size_str(size: int):
    desc = ["B", "kiB", "MiB", "GiB", "TiB"]
    expo = 0
    xsize: float = size
    while xsize >= 1000:
        xsize /= 1024
        expo += 1
    return f"{xsize:.2f} {desc[expo]}"


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


class DetectedProperty(Generic[T]):
    """
    Property that gets initialized by a different method

    Works like functools.cached_property, but useful when one method
    is responsible for a number of properties:

    class Example:
        def detect(self):
            self.x = "Foo"
            self.y = "Bar"

        x = DetectedProperty[str](detect)
        y = DetectedProperty[str](detect)
    """
    def __init__(self, func, doc=None):
        self.func = func
        self.attrname = None
        self.__doc__ = doc

    def __set_name__(self, owner, name):
        self.attrname = name

    @overload
    def __get__(self, instance: None, owner=None) -> 'DetectedProperty[T]': ...
    @overload
    def __get__(self, instance: object, owner=None) -> T: ...

    def __get__(self, instance, owner=None) -> Union[T, 'DetectedProperty[T]']:
        if instance is None:
            return self
        self.func(instance)
        return instance.__dict__[self.attrname]
