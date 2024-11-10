
from abc import abstractmethod
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from platform import machine, system
from sys import stderr

from .game import Game
from .ui import create_gui
from .ui.common import AKawarikiUi, DummyProgressUi, MsgType


class App:
    app_root: Path
    overlayns_binary: Path|None
    platform: str

    def __init__(self, app_root):
        self.app_root = Path(app_root).resolve()
        self.platform = f"{system()}-{machine()}".lower()
        self.overlayns_binary = self.app_root / "overlayns-static" \
            if self.platform == "linux-x86_64" else None

    @property
    def dist_path(self) -> Path:
        return self.app_root / "dist"

    # +-------------------------------------------------+
    # Error reporting
    # +-------------------------------------------------+
    def stderr_show_msg(self, type: MsgType, title: str, message: str):
        colors = {
            MsgType.Error: 31,
            MsgType.Warn: 36,
            MsgType.Info: 34,
        }
        print(f"\033[{colors[type]}m{title}\033[0m:" if stderr.isatty() else f"{title}:", file=stderr)
        for line in message.splitlines():
            print('\t', line, file=stderr)

    @cached_property
    def gui(self) -> AKawarikiUi:
        return create_gui()

    def free_gui(self):
        if "gui" in self.__dict__:
            if hasattr(self.gui, "destroy"):
                self.gui.destroy()
            del self.gui

    def show_msg(self, type, title, message):
        self.stderr_show_msg(type, title, message)
        if self.gui:
            self.gui.show_msg(type, title, message)

    def show_error(self, message, title="Kawariki Runtime Error"):
        self.show_msg(MsgType.Error, title, message)

    def show_warn(self, message, title="Kawariki Runtime Warning"):
        self.show_msg(MsgType.Warn, title, message)

    def show_info(self, message, title="Kawariki Runtime"):
        self.show_msg(MsgType.Info, title, message)

    def show_progress(self, text, progress=0, maximum=100, title="Kawariki Runtime"):
        if self.gui and hasattr(self.gui, "show_progress"):
            return self.gui.show_progress(title, text, progress, maximum)
        elif stderr.isatty():
            from .ui.tty import TtyProgress
            return TtyProgress(stderr, title, text, progress, maximum)
        else:
            return DummyProgressUi(title, text, progress, maximum)


class IRuntime:
    @abstractmethod
    def run(self, game: Game, arguments: Sequence[str], *,
            nwjs_name=None, dry=False, sdk=None,
            no_overlayns=False, no_unpack=False,
            renpy_launcher=False) -> int:
        pass

    @abstractmethod
    def get_patcher(self, game: Game):
        pass
