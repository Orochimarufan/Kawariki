# :---------------------------------------------------------------------------:
#   Terminal UI
# :---------------------------------------------------------------------------:

from typing import TextIO
from .common import AKawarikiProgressUi


class TtyProgress(AKawarikiProgressUi):
    _title: str
    _text: str
    _lines: int
    io: TextIO

    def __init__(self, io: TextIO, title, text, progress=0, maximum=100):
        super().__init__(title, text, progress, maximum)
        self.io = io
        self._title = title
        self._text = text

    def begin(self):
        self._update()

    def end(self):
        self._update()
        self.io.write('\n'*self._lines)
        self.io.flush()

    def _update(self, title=None, text=None, progress=None, maximum=None):
        if title is not None:
            self._title = title
        if text is not None:
            self._text = text
        progress = progress if progress is not None else self.progress
        maximum = maximum if maximum is not None else self.maximum
        output = f'[{self._title}] {self._text} ({progress/maximum:.1%})\033[K\r'.replace('\n', '\t\n')
        if nlines := output.count('\n'):
            output += f'\033[{nlines}F'
        self.io.write(output)
        self.io.flush()
        self._lines = nlines
