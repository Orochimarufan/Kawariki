# :---------------------------------------------------------------------------:
#   Godot runtime
# :---------------------------------------------------------------------------:

from collections.abc import Sequence
from functools import cached_property

from ..app import App, IRuntime
from ..game import Game
from ..process import ProcessLaunchInfo
from ..misc import ErrorCode, version_str
from ..distribution import DistributionInfo, Distribution

from .pack import PackReader


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
        return GodotDistro.load_json(self.resources / "versions.json", self.app.dist_path / "godot", self.app.platform)

    def select_version(self, version: Sequence[int] = ()) -> GodotDistro:
        # TODO: Make selectable and such
        versions = sorted(self.versions, key=lambda dist: dist.version, reverse=True)
        for granul in (3, 2, 1):
            ggv = tuple(version[:granul])
            try:
                return next(dist for dist in versions if dist.version[:granul] == ggv)
            except StopIteration:
                pass
        self.app.show_error(f"No Godot distribution available for version {version_str(version)}")
        raise ErrorCode(110)

    # Run
    def run(self, game: Game, arguments: Sequence[str], *, no_overlayns=False, **kwds):
        pack = game.godot_pack
        if not pack:
            raise RuntimeError("Invalid Game instance passed to Godot Runtime")

        with PackReader.open(pack) as reader:
            version = reader.engine_version

        print(f"Found Godot engine version {version_str(version)}")

        try:
            dist = self.select_version(version)
            print(f"Selected '{dist.name}' distribution")
            if not dist.available:
                self.try_download_version(dist)
        except ErrorCode as e:
            return e.code

        proc = ProcessLaunchInfo(self.app, [dist.binary, "--main-pack", pack.name])
        proc.workingdir = game.root

        proc.exec()

    def get_patcher(self, game):
        raise NotImplementedError()
