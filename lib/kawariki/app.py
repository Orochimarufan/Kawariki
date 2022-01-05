
from abc import abstractmethod
from functools import cached_property
from pathlib import Path
from sys import stderr
from typing import Sequence

from .game import Game
from .ui import create_gui
from .ui.common import AKawarikiUi, DummyProgressUi, MsgType


class App:
    def __init__(self, app_root):
        self.app_root = Path(app_root).resolve()

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
        for l in message.split('\n'):
            print('\t', l, file=stderr)

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

    def show_error(self, message, title="RMMV NW.js Runtime Error"):
        self.show_msg(MsgType.Error, title, message)

    def show_warn(self, message, title="RMMV NW.js Runtime Warning"):
        self.show_msg(MsgType.Warn, title, message)

    def show_info(self, message, title="RMMV NW.js Runtime"):
        self.show_msg(MsgType.Info, title, message)

    def show_progress(self, text, progress=0, maximum=100, title="RMMV NW.js Runtime"):
        if self.gui and hasattr(self.gui, "show_progress"):
            return self.gui.show_progress(title, text, progress, maximum)
        else:
            return DummyProgressUi(title, text, progress, maximum)


class IRuntime:
    @abstractmethod
    def run(self, game: Game, arguments: Sequence[str], nwjs_name=None, dry=False, sdk=None) -> int:
        pass
    @abstractmethod
    def get_patcher(self, game: Game):
        pass
