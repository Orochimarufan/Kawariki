from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from functools import cached_property
from os import chdir, environ, execve
from pathlib import Path, PurePath
from shlex import join as shlex_join
from shutil import copy, copyfileobj
from subprocess import call
from sys import stderr, stdout
from tempfile import NamedTemporaryFile, TemporaryDirectory, mkdtemp
from typing import Any, BinaryIO, IO, Literal, NoReturn, TextIO, overload
from warnings import warn

from .app import App
from .utils.exceptiongroup import ExceptionGroup, format_exception

PathLike = str|PurePath


class CleanupErrors(ExceptionGroup):
    pass


class ProcessEnvironment:
    """ Environment to launch processes in """
    app: App
    argv_prepend: list[str]
    environ: dict[str, str]
    workingdir: PathLike|None
    have_overlayns: bool

    _overlayns: list[str]
    _cleanups: list[Callable[[], Any]]

    def __init__(self, app: App, *, no_overlayns=False):
        self.app = app
        self.argv_prepend = []
        self.environ = environ.copy()
        self.workingdir = None
        self._overlayns = []
        self._cleanups = []
        self.have_overlayns = app.overlayns_binary is not None and not no_overlayns

    def prepend_argv(self, *argv_parts: str):
        self.argv_prepend.extend(argv_parts)

    # overlays
    def overlayns_bind(self, src: PathLike, mp: PathLike):
        """ Bind-mount a path in the executed process using overlayns """
        if ',' in str(src) or ',' in str(mp):
            raise ValueError(
                "Comma in paths is currently not supported by overlayns")
        assert self.have_overlayns
        self._overlayns.append("-m")
        self._overlayns.append(f"bind,{src},{mp}")

    @contextmanager
    def replace_file(self, path: Path, mode: Literal["w", "a"]="w") -> Iterator[IO[str]]:
        """ Replace the content of a file for the process while keeping the original version.
            Either by overlaying using overlayns or by renaming and restoring after process exits.
            Note that the latter option is neither re-entrant nor self-cleaning.
        """
        if path.exists():
            if self.have_overlayns:
                with self.temp_file(prefix=path.stem, suffix=path.suffix) as tf:
                    if mode == "a":
                        with path.open('r') as f:
                            copyfileobj(f, tf)
                    yield tf
                    self.overlayns_bind(tf.name, path)
                return
            backup = path.parent / f"{path.stem}.kawariki-backup{path.suffix}"
            if backup.exists():
                raise FileExistsError(backup)
            print(f"Overwriting {path.name} (Preserved as {backup.name}, will restore after session)")
            path.rename(backup)
            self.at_cleanup(lambda: backup.rename(path))
            if mode == "a":
                copy(backup, path)
        else:
            self.at_cleanup(path.unlink)
        with path.open(mode) as f:
            yield f

    def add_overlays_from_file(self, path: Path):
        """ Add overlay mounts from file. Every line is a -m option """
        with path.open() as f:
            for line in f.readlines():
                line = line.strip()
                if line:
                    self._overlayns.append("-m")
                    self._overlayns.append(line)

    # Temporary files
    @cached_property
    def _tempdir(self) -> TemporaryDirectory:
        tempdir = TemporaryDirectory(prefix="kawariki-")
        print("Created temporary directory: ", tempdir.name)
        self._cleanups.append(tempdir.cleanup)
        return tempdir

    def temp_dir(self, suffix: str|None=None, prefix: str|None=None) -> str:
        """ Create a temporary directory that will be removed on cleanup() """
        return mkdtemp(suffix, prefix, self._tempdir.name)

    @overload
    def temp_file(self, mode: Literal['w', 'w+']="w",
                  buffering: int=-1, encoding: str|None=None, newline: str|None=None,
                  suffix: str|None=None, prefix: str|None=None, delete=False, **kwds) -> TextIO:
        ...

    @overload
    def temp_file(self, mode: Literal['wb', 'w+b'],
                  buffering: int=-1, encoding: str|None=None, newline: str|None=None,
                  suffix: str|None=None, prefix: str|None=None, delete=False, **kwds) -> BinaryIO:
        ...

    def temp_file(self, mode: Literal['w', 'w+', 'wb', 'w+b']="w",
                  buffering: int=-1, encoding: str|None=None, newline: str|None=None,
                  suffix: str|None=None, prefix: str|None=None, delete=False, **kwds) -> IO[Any]:
        """ Create a temporary file that will be removed on cleanup() """
        return NamedTemporaryFile(mode,  # noqa: SIM115 # Caller should use context manager
                                  buffering, encoding, newline,
                                  suffix, prefix, self._tempdir.name,
                                  delete, **kwds)

    # Cleanup
    def at_cleanup(self, cb: Callable[[], Any]) -> None:
        """ Run function at cleanup time """
        self._cleanups.append(cb)

    def cleanup(self) -> None:
        """ Run all cleanup operations """
        errs = []
        for cleanup in reversed(self._cleanups):
            try:
                cleanup()
            except Exception as e:
                errs.append(e)
        self._cleanups.clear()
        if errs:
            raise CleanupErrors("Errors cleaning up process environment", errs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()

    def __del__(self):
        if self._cleanups:
            warn(f"Never cleaned up {self}", ResourceWarning, stacklevel=0)
            try:
                self.cleanup()
            except Exception as e:
                print(f"Cleanup errors:\n{format_exception(e)}")


# TODO: Split out completely and make environment reusable
class ProcessLaunchInfo(ProcessEnvironment):
    """ Collects information needed to execute a process """

    argv: list[PathLike]

    def __init__(self, app: App, argv: Sequence[PathLike], *, no_overlayns=False):
        super().__init__(app, no_overlayns=no_overlayns)
        self.argv = list(argv)

    # Arguments
    def argv_strs(self):
        """ Return the argv with all arguments ensured to be strings """
        return [str(arg) for arg in self.argv]

    def argv_join(self):
        """ Return a joined string version of the argv """
        return shlex_join(map(str, self.argv))

    # Execution
    def _prepare(self) -> tuple[list[str], dict[str, str]]:
        argv = [str(x) for x in self.argv]
        env = self.environ.copy()

        # Grab environment vars from cmdline
        while "=" in argv[0]:
            k, v = argv.pop(0).split('=', 1)
            env[k] = v

        argv = [*self.argv_prepend, *argv]

        # Add overlayns if necessary
        argv = [str(self.app.overlayns_binary), *self._overlayns,  "--", *argv] \
            if self._overlayns else argv

        return argv, env

    def exec(self) -> NoReturn:
        argv, env = self._prepare()

        print(f"Executing [{shlex_join(argv)}] in '{self.workingdir}'")

        # Free resources & flush IO
        self.app.free_gui()
        for f in stdout, stderr:
            f.flush()

        # Do exec
        if not self._cleanups:
            if self.workingdir is not None:
                chdir(self.workingdir)
            execve(argv[0], argv, env)
        else:
            try:
                exit(call(argv, cwd=self.workingdir, env=env))
            finally:
                self.cleanup()

    # TODO: add a call() variant that isn't NoReturn()
