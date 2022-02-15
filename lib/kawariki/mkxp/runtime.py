# :---------------------------------------------------------------------------:
#   Mkxp-z runtime
# :---------------------------------------------------------------------------:

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Sequence

from ..app import App, IRuntime
from ..game import Game
from ..process import ProcessLaunchInfo


class Runtime(IRuntime):
    app: App

    def __init__(self, app: App):
        self.app = app
        # TODO: make it selectable, like nwjs versions
        self.mkxp_version = "mkxp-z_2.3.0_x64"
        self.mkxp_dir = app.app_root / "mkxp"
        self.mkxp_binary = self.mkxp_dir / "dist" / self.mkxp_version / "mkxp-z.x86_64"
        self.preload_path = self.mkxp_dir / "preload.rb"

    def make_mkxp_config(self, game: Game) -> str:
        config: Dict[str, Any] = {
            "preloadScript": [str(self.preload_path)],
        }

        ri = game.rpgmaker_info
        if ri is not None and ri[0] in ("XP", "VX", "VXAce"):
            # This is important for preload to be able to read it from System::CONFIG
            config["rgssVersion"] = ri[1][0]

        hint = game.binary_name_hint
        if hint is not None and hint not in (".", "Game.exe"):
            if hint.endswith(".exe"):
                config["execName"] = hint[:-4]

        # TODO: make this global instead
        if (fpath := game.root / "kawariki-mkxp.json").exists():
            with open(fpath) as f:
                # XXX: should this check and disallow overriding preloadScript etc?
                config.update(json.load(f))

        # TODO: add explicit config for RTP. Is it possible to auto-detect games that need it?
        return json.dumps(config)

    def overlay_file(self, proc: ProcessLaunchInfo, path: Path, content: str, no_overlayns: bool):
        """ Replace the content of a file for the process while keeping the original version.
            Either by overlaying using overlayns or by renaming and restoring after process exits.
            Note that the latter option isn't re-entrant. """
        if path.exists():
            if not no_overlayns:
                with proc.temp_file(prefix=path.stem, suffix=path.suffix) as tf:
                    tf.write(content)
                    proc.overlayns_bind(tf.name, path)
                    return
            backup = path.parent / f"{path.stem}.kawariki-backup{path.suffix}"
            if backup.exists():
                raise FileExistsError(backup)
            path.rename(backup)
            proc.at_cleanup(lambda: backup.rename(path))
        else:
            proc.at_cleanup(path.unlink)
        with open(path, "w") as f:
            f.write(content)

    def run(self, game: Game, arguments: Sequence[str], *, no_overlayns=False, **kwds):
        proc = ProcessLaunchInfo(self.app, [self.mkxp_binary])
        proc.environ["SRCDIR"] = str(game.root)
        proc.environ["LD_LIBRARY_PATH"] = self.mkxp_binary.parent
        proc.workingdir = game.root

        self.overlay_file(proc, game.root / "mkxp.json", self.make_mkxp_config(game), no_overlayns)

        proc.exec()

    def get_patcher(self, game):
        raise NotImplementedError()
