from __future__ import annotations

from functools import cached_property
from os import chdir, environ, execve
from pathlib import PurePath
from shlex import join as shlex_join
from subprocess import call
from sys import stderr, stdout
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import (IO, Any, BinaryIO, Callable, Literal, MutableMapping,
                    NoReturn, Optional, Sequence, TextIO, Union, overload)

from .app import App

PathLike = Union[str, PurePath]


class ProcessLaunchInfo:
    """ Collects information needed to execute a process """

    app: App
    argv: Sequence[PathLike]
    environ: dict[str, str]
    workingdir: Optional[PathLike]
    _overlayns: list[str]
    _cleanups: list[Callable[[], Any]]

    def __init__(self, app: App, argv: Sequence[PathLike]):
        self.app = app
        self.argv = argv
        self.environ = environ.copy()
        self.workingdir = None
        self._overlayns = []
        self._cleanups = []

    # Arguments
    def argv_prepend(self, *argv_part: str):
        self.argv = [*argv_part, *self.argv]

    def argv_append(self, *argv_part: str):
        self.argv = [*self.argv, *argv_part]

    def argv_strs(self):
        """ Return the argv with all arguments ensured to be strings """
        return [str(arg) for arg in self.argv]

    def argv_join(self):
        """ Return a joined string version of the argv """
        return shlex_join(map(str, self.argv))

    # overlayns
    def overlayns_bind(self, src: PathLike, mp: PathLike):
        """ Bind-mount a path in the executed process using overlayns """
        if ',' in str(src) or ',' in str(mp):
            raise ValueError(
                "Comma in paths is currently not supported by overlayns")
        self._overlayns.append("-m")
        self._overlayns.append(f"bind,{src},{mp}")

    # Temporary files
    @cached_property
    def _tempdir(self) -> TemporaryDirectory:
        tempdir = TemporaryDirectory()
        self._cleanups.append(tempdir.cleanup)
        return tempdir

    def temp_dir(self, suffix: Optional[str] = None, prefix: Optional[str] = None) -> TemporaryDirectory:
        """ Create a temporary directory that will be removed on cleanup() """
        return TemporaryDirectory(suffix, prefix, self._tempdir.name)

    @overload
    def temp_file(self, mode: Union[Literal['w'], Literal['w+']] = "w",
                  buffering: int = -1, encoding: Optional[str] = None, newline: Optional[str] = None,
                  suffix: Optional[str] = None, prefix: Optional[str] = None, delete=False, **kwds) -> TextIO:
        ...

    @overload
    def temp_file(self, mode: Union[Literal['wb'], Literal['w+b']],
                  buffering: int = -1, encoding: Optional[str] = None, newline: Optional[str] = None,
                  suffix: Optional[str] = None, prefix: Optional[str] = None, delete=False, **kwds) -> BinaryIO:
        ...

    def temp_file(self, mode: Union[Literal['w'], Literal['w+'], Literal['wb'], Literal['w+b']] = "w",
                  buffering: int = -1, encoding: Optional[str] = None, newline: Optional[str] = None,
                  suffix: Optional[str] = None, prefix: Optional[str] = None, delete=False, **kwds) -> IO[Any]:
        """ Create a temporary file that will be removed on cleanup() """
        return NamedTemporaryFile(mode, buffering, encoding, newline, suffix, prefix, self._tempdir.name, delete, **kwds)

    # Execution
    def _prepare(self) -> tuple[list[str], dict[str, str]]:
        argv = [str(x) for x in self.argv]
        env = self.environ.copy()

        # Grab environment vars from cmdline
        while "=" in argv[0]:
            k, v = argv.pop(0).split('=', 1)
            env[k] = v

        # Add overlayns if necessary
        argv = [str(self.app.overlayns_binary), *self._overlayns,  "--", *argv] \
            if self._overlayns else argv

        return argv, env

    def exec(self) -> NoReturn:
        argv, env = self._prepare()

        print(f"Executing {shlex_join(argv)}")

        # Free resources & flush IO
        self.app.free_gui()
        for f in stdout, stderr:
            f.flush()

        # Do exec
        if not self.cleanup:
            if self.workingdir is not None:
                chdir(self.workingdir)
            execve(argv[0], argv, env)
        else:
            try:
                exit(call(argv, cwd=self.workingdir, env=env))
            finally:
                self.cleanup()

    # TODO: add a call() variant that isn't NoReturn()

    # Cleanup
    def at_cleanup(self, cb: Callable[[], Any]):
        self._cleanups.append(cb)

    def cleanup(self):
        for cleanup in self._cleanups:
            cleanup()
