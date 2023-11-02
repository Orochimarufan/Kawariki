# :---------------------------------------------------------------------------:
#   Tk UI
# :---------------------------------------------------------------------------:

from .common import AKawarikiProgressUi, AKawarikiUi, MsgType

import tkinter.messagebox
import tkinter.ttk


class TkProgressDialog(AKawarikiProgressUi):
    def __init__(self, title, text, progress=0, maximum=100):
        super().__init__(title, text, progress, maximum)
        dialog = self.dialog = tkinter.Toplevel(None)#tkinter._get_default_root('create dialog window'))
        dialog.withdraw()
        dialog.title(title)
        #dialog.wm_attributes("-type", "dialog")
        self.body = tkinter.Frame(dialog)
        self.body.pack(padx=5, pady=5)
        self.label = tkinter.Label(self.body, text=text)
        self.label.grid(row=0, column=0)
        self.progress_var = tkinter.DoubleVar(value=progress)
        self.progress_bar = tkinter.ttk.Progressbar(self.body, variable=self.progress_var, maximum=maximum, length=600)
        self.progress_bar.grid(row=1, column=0)

    def begin(self):
        self.dialog.deiconify()
        self.body.focus_set()
        self.dialog.grab_set()
        self._update()

    def end(self):
        self._update()
        self.dialog.withdraw()
        self.dialog.destroy()

    def _update(self, title=None, text=None, progress=None, maximum=None):
        if title is not None:
            self.dialog.title(title)
        if text is not None:
            self.label.configure(text=text)
        if maximum is not None:
            self.progress_bar.configure(max=maximum)
        if progress is not None:
            self.progress_var.set(progress)
        self.dialog.update()
        self.dialog.update_idletasks()


class TkGui(AKawarikiUi):
    def show_msg(self, type, title, message):
        self._root # hide tk root window
        {
            MsgType.Error: tkinter.messagebox.showerror,
            MsgType.Warn: tkinter.messagebox.showwarning,
            MsgType.Info: tkinter.messagebox.showinfo,
        }[type](title, message)

    @property
    def _root(self):
        self.__dict__["_root"] = root = tkinter.Tk()
        root.withdraw()
        root.update()
        return root

    def destroy(self):
        if "_root" in self.__dict__:
            self._root.destroy()
            del self.__dict__["_root"]

    def show_progress(self, *args, **kwds):
        self._root # Make sure root is hidden
        return TkProgressDialog(*args, **kwds)

