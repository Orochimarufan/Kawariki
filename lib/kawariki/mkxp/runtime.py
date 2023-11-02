# :---------------------------------------------------------------------------:
#   Mkxp-z runtime
# :---------------------------------------------------------------------------:

import json
from pathlib import Path
from typing import Any, Dict, Sequence, Literal
from functools import cached_property

from ..app import App, IRuntime
from ..game import Game
from ..process import ProcessLaunchInfo
from ..misc import ErrorCode
from ..distribution import DistributionInfo, Distribution


class MKXPDistributionInfo(DistributionInfo):
    variant: Literal["mkxp-z"]


class MKXP(Distribution):
    info: MKXPDistributionInfo

    @property
    def variant(self) -> str:
        return self.info["variant"]

    @property
    def slug(self) -> str:
        return f"{self.variant}-{self.version_str}-{self.platform}"


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
        from ..download import download_dist_progress_tar

        download_dist_progress_tar(self.app, version)

        self.app.show_info(f"Finished downloading MKXP distribution '{version.name}'")

    @cached_property
    def mkxp_versions(self):
        return MKXP.load_json(self.mkxp_dir / "versions.json", self.app.dist_path / "mkxp", self.app.platform)

    def get_mkxp_version(self):
        # TODO: Make selectable and such
        ver = self.mkxp_versions[0]
        if not ver.available:
            self.try_download_version(ver)
        return ver

    # Run
    def make_mkxp_config(self, version: MKXP, game: Game) -> str:
        config: Dict[str, Any] = {}

        # RGSS version
        try:
            # This is important for preload to be able to read it from System::CONFIG
            config["rgssVersion"] = ("XP", "VX", "VXAce").index(game.rpgmaker_release)+1
        except ValueError:
            pass

        # Executable base name
        hint = game.binary_name_hint
        if hint is not None and hint.lower() not in (".", "game.exe"):
            if hint.endswith(".exe"):
                config["execName"] = hint[:-4]

        # Load defaults from config file
        def update_from(fpath: Path, *, exclude=frozenset(), merge=True):
            if fpath.exists():
                with open(fpath) as f:
                    for k,v in json.load(f).items():
                        if k in exclude:
                            continue
                        elif k == "rgssVersion" and v == 0:
                            # Never overwrite version with 0
                            continue
                        elif merge and isinstance(v, list):
                            # Merge lists
                            config.setdefault(k, []).extend(v)
                        else:
                            config[k] = v

        update_from(game.root / "mkxp.json")
        update_from(self.mkxp_dir / "mkxp.json", exclude={"rgssVersion", "gameFolder", "iconPath", "customScript", "execName"})
        update_from(game.root / "kawariki-mkxp.json")

        # Preload
        config.setdefault("preloadScript", []).append(str(self.preload_path))

        # TODO: add explicit config for RTP. Is it possible to auto-detect games that need it?
        return json.dumps(config)

    def run(self, game: Game, arguments: Sequence[str], *, no_overlayns=False, **kwds):
        mkxp = self.get_mkxp_version()

        proc = ProcessLaunchInfo(self.app, [mkxp.binary], no_overlayns=no_overlayns)
        proc.environ["SRCDIR"] = str(game.root)
        proc.environ["LD_LIBRARY_PATH"] = mkxp.path
        proc.workingdir = game.root

        conf = self.make_mkxp_config(mkxp, game)
        with proc.replace_file(game.root / "mkxp.json") as f:
            f.write(conf)

        proc.exec()

    def get_patcher(self, game):
        raise NotImplementedError()
