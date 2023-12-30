from functools import cached_property
from typing import Optional, Sequence

from ..app import App, IRuntime
from ..distribution import Distribution
from ..game import Game
from ..misc import ErrorCode
from ..process import ProcessLaunchInfo
from .detect import RenpyVersion


class Runtime(IRuntime):
    app: App

    def __init__(self, app: App):
        self.app = app
        self.resources = app.app_root / "renpy"

    # Runtime Versions
    def try_download_version(self, version: Distribution):
        """
        Download distribution

        :param version: The version to download
        :raise ErrorCode: on error
        """
        from ..download import download_dist_progress_tar

        download_dist_progress_tar(self.app, version)

        self.app.show_info(f"Finished downloading Ren'Py distribution '{version.name}'")

    @cached_property
    def versions(self) -> Sequence[Distribution]:
        return Distribution.load_json(
            self.resources / "versions.json",
            self.app.dist_path / "renpy",
            self.app.platform)

    def select_version(self, gamever: RenpyVersion) -> Optional[Distribution]:
        # Try to match MAJOR.MINOR version if possible, then try latest available for MAJOR
        for granul in (2, 1):
            ggv = gamever.version_info[:granul]
            if v := sorted((dist for dist in self.versions if dist.version[:granul] == ggv),
                           key=lambda dist: dist.version):
                return v[-1]
        # XXX: Allow manual selection, upgrading to latest compatible?
        return None

    # Run
    def run(self, game: Game, arguments: Sequence[str], *, no_overlayns=False, **kwds):
        gamever = game.renpy_version
        if not gamever:
            self.app.show_error("Could not determine Ren'Py engine version")
            raise ErrorCode(12)

        print(f"Found Ren'Py {gamever.version} '{gamever.version_name}'")
        dist = self.select_version(gamever)
        if not dist:
            self.app.show_error(f"Could not find compatible Ren'Py SDK for {gamever.version}")
            raise ErrorCode(11)

        print(f"Selected distribution: {dist.name}")

        if not dist.available:
            try:
                self.try_download_version(dist)
            except ErrorCode as e:
                return e.code

        proc = ProcessLaunchInfo(self.app, [dist.binary, game.root])
        proc.workingdir = game.root

        proc.exec()

    def get_patcher(self, game):
        raise NotImplementedError()
