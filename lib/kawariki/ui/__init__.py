# :---------------------------------------------------------------------------:
#   UI
# :---------------------------------------------------------------------------:

from importlib.util import find_spec
from os import environ
from shutil import which

from .common import AKawarikiUi

# Tkinter check
_HAVE_TK = None

def have_tkinter() -> bool:
    global _HAVE_TK
    if _HAVE_TK is None:
        _HAVE_TK = find_spec("tkinter") is not None
    return _HAVE_TK


# Dynamic creation
def _try_create_gui(what):
    if what == "tkinter":
        if have_tkinter():
            from .tkinter import TkGui
            return TkGui()
    elif what == "zenity":
        prog = which("zenity")
        if prog:
            from .external import ZenityGui
            return ZenityGui(prog)
    elif what == "kdialog":
        prog = which("kdialog")
        if prog:
            from .external import KDialogGui
            return KDialogGui(prog)
    else:
        raise KeyError(what)

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
                print("Warning: Explicitly requested %s GUI, but %s not available" % (name, req)) # noqa: UP031
                break
        else:
            print("Warning: Unknown value for KAWARIKI_GUI: %s" % specified)

    # Try to use any implementation
    for ss, _, _ in _GUI_OPTOINS:
        if gui := _try_create_gui(ss[0]):
            return gui
    else:
        print("Warning: Could not find any suitable GUI, need any of: %s" % " or ".join(x[2] for x in _GUI_OPTOINS))
