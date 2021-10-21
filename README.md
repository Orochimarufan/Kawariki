Kawariki NW.js runtime/compatibility tool
=========================================

Kawariki is a Steam Play compatible tool for running NW.js-based games using
different (usually newer) versions of NW.js than they shipped with.
This includes running games that only have a Windows build on a linux-native version.
Support for patching Greenworks natives is included.

Requires at least Python 3.8.

Usage
-----

### Steam Play
Just install it into compatibilitytools.d like a custom Proton release. You can then
select it in the game properties dialog. You shouldn't set it globally in the settings
dialog as it only works with NW.js-based games, not general Windows titles.

Some environment variables are available to influence Kawariki:
- `KAWARIKI_SDK=1` Use NW.js with DevTools support (like `--sdk`)
- `KAWARIKI_NWJS=<name>` Use a specific NW.js version (like `--nwjs <name>`)

These can be used in the Steam launch options like with Proton. E.g. `KAWARIKI_SDK=1 %command%`

### CLI
The CLI brings some options for non-Steam games and developers:

- `./kawariki run <path-to-game>` will try to run a game with custom NW.js (As trough Steam Play)
- `./kawariki launcher <path-to-game> [filename]` Will create a launcher script in the game folder that runs the game trough Kawariki
- `./kawariki patch <path-to-game> -o <new-path>` Makes a copy of the game with replaced NW.js

For more info see `./kawariki --help`

RPGMaker MV and MZ
------------------

While RPGMaker MV and MZ (for the first time) support exporting
to Linux, many developers do not use this option and some report
issues with it. However, it appears they are based on
an unmodified NW.js runtime and it is a viable strategy
to run Windows exports on a native runtime procured directly
from the NW.js project. This obviously doesn't extend to
any native node modules (like Greenworks)

This is an attempt to build a Steam Play compatible compatibilitytool
that runs RPGMaker MV/MZ games in a native NW.js runtime.
It may work with other NW.js based games as well.

Greenworks
----------

Some support is included for Greenworks (NW.js Steamworks library).
This is achieved by trying to replace the game's greenworks library
with one that includes the correct linux native modules.

To avoid modifying the game installation, Linux namespaces are used
to 'overlay' the custom greenworks files over the install directory.

This requires unprivileged user namespaces to be enabled in the kernel
For example, In some versions of Ubuntu/Debian it can be enabled with
`sysctl -w kernel.unprivileged_userns_clone=1`

The required files can be gotten from the relevant Steam Partner pages
and https://greenworks-prebuilds.armaldio.xyz/ or built from source.

overlayns-static
----------------

The overlayns binary works similarly to unshare(1) except it allows
mounts to be specified on the commandline.

nwjs-versions.json
------------------

This file specifies the NW.js versions that should be considered.
Available keys are:
- `version` *required array-of-numbers* The NW.js version of this distribution (e.g. `[0,54,1]`)
- `dist` *required string* The name of the directory the distribution is stored in.
- `dist_url` *string* An URL to download the distribution from if not already available. It must point to a gzip/bzip2/xz compressed tar-archive.
- `name` *string* An optional name given to the distribution for use with `--nwjs`. Defaults to the value of `dist`.
- `sdk` *boolean* Wether the distribution is a SDK release (i.e. includes DevTools). Defaults to `false`.
- `greenworks` *string* Name of a directory containing compatible replacements for the greenworks library. Greenworks is not supported if omitted.

By default, the most recent NW.js distribution listed is chosen.

License
-------

The code itself (kawariki) is GPL3+. Generated files like launcher scripts shall be CC0.
NW.js, Greenworks and Steamworks have their respective licenses.
