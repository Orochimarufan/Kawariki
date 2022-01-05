# :---------------------------------------------------------------------------:
#   UI
# :---------------------------------------------------------------------------:

from .common import MsgType, AKawarikiUi

from shutil import which
from os import environ


# Tkinter check
_HAVE_TK = None

def have_tkinter() -> bool:
    global _HAVE_TK
    if _HAVE_TK is None:
        try:
            import tkinter.ttk
        except ImportError:
            _HAVE_TK = False
        else:
            _HAVE_TK = True
    return _HAVE_TK


# Dynamic creation
def _try_create_gui(what):
    if what == "tkinter":
        if have_tkinter():
            from .tkinter import TkGui
            return TkGui()
    elif what == "zenity":
        if (prog := which("zenity")):
            from .external import ZenityGui
            return ZenityGui(prog)
    elif what == "kdialog":
        if (prog := which("kdialog")):
            from .external import KDialogGui
            return KDialogGui(prog)

_GUI_OPTOINS = [
            (("tkinter", "tk"), "Tkinter", "tkinter package"),
            (("zenity",), "Zenity", "zenity executable"),
            (("kdialog",), "KDialog", "kdialog executable")]


def create_gui() -> AKawarikiUi:
    # Try to use specific implementation
    specified = environ.get("KAWARIKI_GUI", "").lower()
    if specified:
        for ss, name, req in _GUI_OPTOINS:
            if specified in ss:
                if gui := _try_create_gui(ss[0]):
                    return gui
                print("Warning: Explicitly requested %s GUI, but %s not available" % (name, req))
                break
        else:
            print("Warning: Unknown value for KAWARIKI_GUI: %s" % specified)
    
    # Try to use any implementation
    for ss, _, _ in _GUI_OPTOINS:
        if gui := _try_create_gui(ss[0]):
            return gui
    else:
        print("Warning: Could not find any suitable GUI, need any of: %s" % " or ".join(x[2] for x in _GUI_OPTOINS))
