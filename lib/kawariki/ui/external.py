# :---------------------------------------------------------------------------:
#   UI using external processes
# :---------------------------------------------------------------------------:

import subprocess

from .common import MsgType, AKawarikiUi, AKawarikiProgressUi, DummyProgressUi


class ZenityGui(AKawarikiUi):
    def __init__(self, prog):
        self.prog = prog

    def show_msg(self, type, title, message):
        types = {
            MsgType.Error: "--error",
            MsgType.Warn: "--warning",
            MsgType.Info: "--info",
        }
        subprocess.check_call([self.prog, types[type], "--title", title, "--text", message])

    class ProgressDialog:
        # TODO: Fix newline in text
        def __init__(self, prog, /, title, text, progress=0, maximum=100):
            self.prog = prog
            self.title = title
            self._text = text
            self._progress = progress
            self.maximum = maximum
            self.proc = None

        @property
        def percentage(self):
            return self._progress * 100 // self.maximum

        def __enter__(self):
            self.proc = subprocess.Popen([self.prog, "--progress", "--no-cancel", "--auto-close",
                "--title", self.title, "--text", self._text, "--percentage", f"{self.percentage}"],
                stdin=subprocess.PIPE)
            return self

        def __exit__(self, t, e, tb):
            self.proc.stdin.close()
            self.proc.wait()

        @property
        def progress(self):
            return self._progress

        @progress.setter
        def progress(self, progress):
            self._progress = progress
            if self.proc:
                self.proc.stdin.write(f"{self.percentage:.0f}\n".encode("utf-8"))
                self.proc.stdin.flush()

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, text):
            self._text = text
            if self.proc:
                self.proc.stdin.write(f"#{text}\n".encode("utf-8"))
                self.proc.stdin.flush()

    def show_progress(self, *args, **kwds):
        return self.ProgressDialog(self.prog, *args, **kwds)


class KDialogGui:
    def __init__(self, prog):
        self.prog = prog

    def show_msg(self, type, title, message):
        types = {
            MsgType.Error: "--error",
            MsgType.Warn: "--warn",
            MsgType.Info: "--info",
        }
        return subprocess.check_call([self.prog, "--title", title, types[type], message])
