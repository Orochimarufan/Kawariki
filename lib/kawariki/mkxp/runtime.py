# :---------------------------------------------------------------------------:
#   Mkxp-z runtime
# :---------------------------------------------------------------------------:

import json
from pathlib import Path
from typing import Any, Dict, Sequence
from functools import cached_property

from ..app import App, IRuntime
from ..game import Game
from ..process import ProcessLaunchInfo
from ..misc import ErrorCode


class MKXP:
    def __init__(self, info, path):
        self._path = path
        self.info = info

    @property
    def version(self):
        return tuple(self.info["version"])

    @property
    def name(self):
        return self.info.get("name", self.dist)

    @property
    def dist(self):
        return self.info["dist"]
    
    @property
    def path(self):
        return self._path / "dist" / self.dist

    def has(self, component):
        return bool(self.info.get(component, None))

    @property
    def binary(self):
        return self.path / "mkxp-z.x86_64"

    @property
    def available(self):
        return self.path.exists()

    def __repr__(self):
        return f"<Runtime.MKXP {version_str(self.version)} '{self.dist}' at 0x{id(self):x}>"


class Runtime(IRuntime):
    app: App

    def __init__(self, app: App):
        self.app = app
        self.mkxp_dir = app.app_root / "mkxp"
        self.preload_path = self.mkxp_dir / "preload.rb"

    # Runtime Versions
    def try_download_version(self, version: MKXP):
        """
        Download mkxp distribution

        :param mkxp: The version to download
        :raise ErrorCode: on error
        """
        from ..download import download_progress_tar

        if not version.has("dist_url"):
            self.app.show_error(f"Cannot download MKXP distribution '{version.dist}'\versions.json doesn't specify a download url.")
            raise ErrorCode(8)
        
        def strip_prefix(entry):
            try:
                index = entry.name.index("/")
            except ValueError:
                # Skip files in archive root
                return False
            entry.name = entry.name[index+1:]

        try:
            download_progress_tar(self.app, version.info["dist_url"], version.path,
                description=f"Downloading NW.js distribution '{version.dist}'",
                modify_entry=strip_prefix)
        except Exception:
            raise ErrorCode(10)

        self.app.show_info(f"Finished downloading MKXP distribution '{version.dist}'")

    @cached_property
    def mkxp_versions(self):
        with open(self.mkxp_dir / "versions.json") as f:
            versions = json.load(f)
        return [MKXP(ver, self.mkxp_dir) for ver in versions]

    def get_mkxp_version(self):
        # TODO: Make selectable and such
        ver = self.mkxp_versions[0]
        if not ver.available:
            self.try_download_version(ver)
        return ver

    # Run
    def make_mkxp_config(self, version: MKXP, game: Game) -> str:
        config: Dict[str, Any] = {
            "preloadScript": [str(self.preload_path)],
        }

        ri = game.rpgmaker_info
        if ri is not None and ri[0] in ("XP", "VX", "VXAce"):
            # This is important for preload to be able to read it from System::CONFIG
            config["rgssVersion"] = ri[1][0]

        hint = game.binary_name_hint
        if hint is not None and hint.lower() not in (".", "game.exe"):
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
            Note that the latter option isn't re-entrant.
            Cannot overlay on top of non-existant file using mounts however. Copying the whole
            containing directory to /tmp to avoid changing the original seems very impractical. """
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
        mkxp = self.get_mkxp_version()

        proc = ProcessLaunchInfo(self.app, [mkxp.binary])
        proc.environ["SRCDIR"] = str(game.root)
        proc.environ["LD_LIBRARY_PATH"] = mkxp.path
        proc.workingdir = game.root

        self.overlay_file(proc, game.root / "mkxp.json", self.make_mkxp_config(mkxp, game), no_overlayns)

        proc.exec()

    def get_patcher(self, game):
        raise NotImplementedError()
