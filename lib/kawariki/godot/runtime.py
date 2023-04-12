# :---------------------------------------------------------------------------:
#   Godot runtime
# :---------------------------------------------------------------------------:

from pathlib import Path
from typing import Any, Dict, Sequence, Literal, Optional
from functools import cached_property

from ..app import App, IRuntime
from ..game import Game
from ..process import ProcessLaunchInfo
from ..misc import ErrorCode, version_str
from ..distribution import DistributionInfo, Distribution


GodotDistro = Distribution[DistributionInfo]


class Runtime(IRuntime):
    app: App

    def __init__(self, app: App):
        self.app = app
        self.resources = app.app_root / "godot"

    # Runtime Versions
    def try_download_version(self, version: GodotDistro):
        """
        Download distribution

        :param version: The version to download
        :raise ErrorCode: on error
        """
        from ..download import download_dist_progress_zip

        download_dist_progress_zip(self.app, version)
        version.binary.chmod(0o755) # Make sure it's executable

        self.app.show_info(f"Finished downloading Godot distribution '{version.name}'")

    @cached_property
    def versions(self) -> Sequence[GodotDistro]:
        return GodotDistro.load_json(self.resources / "versions.json", self.app.dist_path / "godot", self.app.platform, v2=True)

    def select_version(self, filter: Sequence[int] = ()) -> GodotDistro:
        # TODO: Make selectable and such
        matching = [ ver for ver in self.versions if ver.version[:len(filter)] == filter ]
        if not matching:
            self.app.show_error(f"No Godot distribution available for version {version_str(filter)}")
            raise ErrorCode(110)
        ver = matching[0]
        if not ver.available:
            self.try_download_version(ver)
        return ver

    # Run
    def run(self, game: Game, arguments: Sequence[str], *, no_overlayns=False, **kwds):
        try:
            dist = self.select_version()
        except ErrorCode as e:
            return e.code

        pack = game.godot_pack
        if not pack:
            raise RuntimeError("Invalid Game instance passed to Godot Runtime")
        proc = ProcessLaunchInfo(self.app, [dist.binary, "--main-pack", pack.name])
        proc.workingdir = game.root

        proc.exec()

    def get_patcher(self, game):
        raise NotImplementedError()
