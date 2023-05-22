# :---------------------------------------------------------------------------:
#   Game-Specific quirks
# :---------------------------------------------------------------------------:

import os

from .game import Game

XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

STEAM_QUIRKS = {
    "1150690": { # OMORI
        "environ": {
            # LOCALAPPDATA is queried for persistent storage location directly
            # and without fallback, crashing early if it isn't defined
            "LOCALAPPDATA": XDG_CONFIG_HOME,
            # Uses node filesystem API directly and has filename case problems
            "KAWARIKI_NWJS_CIFS": "1",
        },
    },
}
