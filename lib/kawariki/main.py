#!/usr/bin/env python3
# Kawariki -- NW.js game compat tool
# ------------------------------------------------------------------
# Copyright (C) 2021-2022 Taeyeon Mori <taeyeon at oro dot sodimm dot me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------
# Please note that any files handled by this tool
# are covered by their respective third-party licenses.
# Content generated in whole by the tool without being derived from
# third-party distributions shall be in the public domain under CC0.

__version__ = "2.0a0"

import argparse
import importlib
import os
import pathlib
import shlex
import sys

from .misc import ErrorCode, version_str, hardlink_or_copy
from .app import App, IRuntime
from .game import Game
from .quirks import STEAM_QUIRKS


# Common verb entrypoints
def add_launcher(app: App, game: Game, args) -> int:
    from .misc import format_launcher_script

    selfpath = (app.app_root / pathlib.Path(sys.argv[0]).name).resolve()
    prefix = shlex.split(args.prefix) if args.prefix else []

    path = game.root / args.launcher
    try:
        with path.open("x") as f:
            binary_hint = game.binary_name_hint if game.binary_name_hint else "."
            f.write(format_launcher_script(*prefix, selfpath, "run", "--", binary_hint))
    except FileExistsError:
        app.show_error("File already exists. Please choose a different name"
                       f"for the Kawariki launcher or delete it first:\n{path}")
        return 1
    path.chmod(0o755)

    print(f"Created launcher '{path}'")

    return 0


def run_patcher(runtime, game, args) -> int:
    from .patcher.common import APatcherOut
    patcher = runtime.get_patcher(game)

    out: APatcherOut
    if args.archive:
        from .patcher.output.tar import PatcherToTar
        out = PatcherToTar(args.archive)
    elif args.dest:
        from .patcher.output.flat import PatcherToCopy
        out = PatcherToCopy(args.dest)
    elif args.link_dest:
        from .patcher.output.flat import PatcherToCopy
        out = PatcherToCopy(args.link_dest, hardlink_or_copy)
    elif args.inplace:
        from .patcher.output.flat import PatcherInPlace
        out = PatcherInPlace(game.root)
    else:
        assert 0

    patcher.run(out, game)

    return 0


# :---------------------------------------------------------------------------:
#   Main
# :---------------------------------------------------------------------------:
def env_bool(str) -> bool:
    return str.lower() not in ("", "0", "false", "no", "n")

def check_environ(envname, type):
    if (arg := os.environ.get(envname)) is not None:
        print(f"Read argument from environment: {envname}={shlex.quote(arg)}", file=sys.stderr)
        return type(arg)

def add_common_args(parser: argparse.ArgumentParser, env, *, gamepath=True, nwjs=True, sdk=True):
    if gamepath:
        parser.add_argument("game", type=pathlib.Path,
                            help="Path of the game directory or executable")
    parser.add_argument("--runtime", choices=("nwjs", "mkxp", "renpy", "godot"), default=env.get("runtime"),
                        help="Manually select Kawariki runtime")
    parser.add_argument("--no-overlayns", action="store_true", default=env.get("no_overlayns"),
                        help="Don't try to use linux user namespaces")
    # NW.js
    nwjs_ = parser.add_argument_group("NW.js Runtime")
    if sdk:
        nwjs_.add_argument("-d", "--sdk", action="store_true", default=env.get("sdk"),
                           help="Select a NW.js version with DevTools support")
    if nwjs:
        nwjs_.add_argument("--nwjs", default=env.get("nwjs"),
                           help="Use specified NW.js version from 'nwjs-versions.json'")
    nwjs_.add_argument("--no-unpack", action="store_true",
                       help="Don't allow unpacking packaged apps to a temporary directory")
    # Ren'Py
    renpy = parser.add_argument_group("Ren'Py Runtime")
    renpy.add_argument("--renpy-launcher", action="store_true",
                       help="Start Ren'Py Launcher instead of the game")

def parse_args(argv, env):
    # Parse commandline
    parser = argparse.ArgumentParser(prog=argv[0], description="""\
    Kawariki is a Steam Play compatible tool for running NW.js-based games using
    different (usually newer) versions of NW.js than they shipped with.
    This includes running games that only have a Windows build on a linux-native version.
    Support for patching Greenworks natives is included.""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version",
            version=f"Kawariki {__version__}, running on Python {version_str(sys.version_info)}")
    sub = parser.add_subparsers(dest="action")

    def add_sub_parser(name, help=None):
        return sub.add_parser(name, help=help, description=help)

    # Arguments for run mode
    run = add_sub_parser("run", help="Run a NW.js based game on a different NW.js version")
    add_common_args(run, env)
    run.add_argument("--wait", action="store_true")
    run.add_argument("--dry", action="store_true",
                     help="Only print the resulting command, don't run the game")
    run.add_argument("game_args", nargs="*",
                     help="Pass additional arguments to the game", metavar="game args")

    # Fixpath
    fixpath = add_sub_parser("fixpath")
    fixpath.add_argument("path")

    # Arguments for patch mode
    patchgame = add_sub_parser("patch",
                               help="Create a patched version of a NW.js game with a different version baked in")
    add_common_args(patchgame, env)
    patchgame_out = patchgame.add_argument_group("destination options").add_mutually_exclusive_group(required=True)
    patchgame_out.add_argument("-a", "--archive", type=pathlib.Path,
                               help="Create an archive file")
    patchgame_out.add_argument("-o", "--dest", type=pathlib.Path,
                               help="Store patched game in this directory")
    patchgame_out.add_argument("--link-dest", type=pathlib.Path,
                               help="Store patched game in this directory, use hard links to save space")
    patchgame_out.add_argument("--inplace", action="store_true",
                               help="Modify the game in place")

    # Arguments for launcher mode
    create_launcher = add_sub_parser("launcher",
                                     help="Add a launcher script to the game directory")
    add_common_args(create_launcher, env)
    create_launcher.add_argument("-p", "--prefix",
                                 help="Prefix the command to run (e.g. primusrun/gamemode/gamescope)")
    create_launcher.add_argument("launcher", nargs="?", default="Game.sh",
                                 help="Filename of the launcher to create [%(default)s]")

    return parser.parse_args(argv[1:])

def main(app, argv) -> int:
    # Get defaults from environment variables
    env = {
        "sdk": check_environ("KAWARIKI_SDK", env_bool),
        "nwjs": check_environ("KAWARIKI_NWJS", str),
        "no_overlayns": check_environ("KAWARIKI_NO_OVERLAYNS", env_bool),
        "no_unpack": check_environ("KAWARIKI_NO_UNPACK", env_bool),
        "runtime": check_environ("KAWARIKI_RUNTIME", str),
    }

    args = parse_args(argv, env)

    # -------------------------------------------
    if args.action == "fixpath":
        # Running native NW.js, try to strip out any backslashes that may have slipped in
        sys.stdout.buffer.write(pathlib.PureWindowsPath(args.path).as_posix().encode("utf-8"))
        return 0

    print(f"v{__version__}, python {version_str(sys.version_info)}; {shlex.join(argv[1:])}", file=sys.stderr)

    if args.action == "run" and args.game.name in {"iscriptevaluator.exe", "d3ddriverquery64.exe"}:
        # Skip install scripts.
        print(f"Skipping {args.game.name} invocation", file=sys.stderr)
        return 0

    # Assume backslashes should actually be forward slashes
    if '\\' in str(args.game):
        game_root = pathlib.Path(pathlib.PureWindowsPath(args.game).as_posix()).resolve()
    else:
        game_root = args.game.resolve()

    game_exe = None
    if not game_root.is_dir():
        game_exe = game_root.name
        game_root = game_root.parent

    game = Game(game_root, game_exe)

    if args.action == "launcher":
        return add_launcher(app, game, args)

    # TODO: Do this better. It really shouldn't mess with the global environ
    quirk = STEAM_QUIRKS.get(game.steam_appid or "", None)
    if quirk is not None:
        print(f"Using quirks for Steam appid: {game.steam_appid}")
        if 'environ' in quirk:
            os.environ.update(quirk['environ'])

    # Check game type
    if args.runtime in (None, "auto"):
        if game.is_nwjs_app:
            args.runtime = "nwjs"
        elif game.is_rpgmaker_rgss:
            args.runtime = "mkxp"
        elif game.is_godot:
            args.runtime = "godot"
        elif game.is_renpy:
            args.runtime = "renpy"
        else:
            app.show_error(f"Couldn't detect Kawariki runtime for game: {game_root}")
            return 22
    try:
        runtime_module = importlib.import_module(f".{args.runtime}.runtime", __package__)
    except ImportError:
        app.show_error(f"Could not load runtime '{args.runtime}'")
        return 22
    runtime: IRuntime = runtime_module.Runtime(app)

    if args.action == "run":
        # Ignore --wait for now
        try:
            return runtime.run(game, args.game_args,
                               nwjs_name=args.nwjs, dry=args.dry, sdk=args.sdk,
                               no_overlayns=args.no_overlayns, no_unpack=args.no_unpack,
                               renpy_launcher=args.renpy_launcher)
        except ErrorCode as e:
            return e.code
    elif args.action == "patch":
        return run_patcher(runtime, game, args)
    else:
        print("Need a verb")
        return 1


