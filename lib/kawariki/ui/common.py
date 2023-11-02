# :---------------------------------------------------------------------------:
#   Ui Common
# :---------------------------------------------------------------------------:

import enum
import abc


class MsgType(enum.Enum):
    Error = 0
    Warn = 1
    Info = 2


def _setter_only(fn):
        return property(None, fn)


class AKawarikiProgressUi:
    def __init__(self, title: str, text: str, progress=0, maximum=100):
        self._progress = progress
        self._maximum = maximum

    # Abstract
    def begin(self):
        pass

    @abc.abstractmethod
    def _update(self, *, title=None, text=None, progress=None, maximum=None):
        pass

    def end(self):
        pass

    # Property interface
    def update(self, *, title=None, text=None, progress=None, maximum=None):
        self._update(title, text, progress, maximum)
        if progress is not None:
            self._progress = progress
        if maximum is not None:
            self._maximum = maximum

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, et, e, tb):
        self.end()

    @_setter_only
    def title(self, value):
        self.update(title=value)

    @_setter_only
    def text(self, value):
        self.update(text=value)

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self.update(progress=value)

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        self.update(maximum=value)


class DummyProgressUi(AKawarikiProgressUi):
    def _update(self, t, x, p, m):
        pass


class AKawarikiUi:
    @abc.abstractmethod
    def show_msg(self, type: MsgType, title: str, message: str):
        pass

    @abc.abstractmethod
    def show_progress(self, title: str, text: str, progress: int=0, maximum: int=100) -> AKawarikiProgressUi:
        pass

    def destroy(self):
        pass
