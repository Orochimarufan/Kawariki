Kawariki runtime/compatibility tool
===================================

Kawariki is a Steam Play compatible tool for running games using
different (usually newer) versions of their engine than they shipped with.
This includes running games that only have a Windows build on a linux-native version.

Requires at least Python 3.8.

Usage
-----

### Steam Play
Just install it into compatibilitytools.d like a custom Proton release. You can then
select it in the game properties dialog. You shouldn't set it globally in the settings
dialog as it doesn't try to handle arbitrary Windows games.

Some environment variables are available to influence Kawariki.
These can be used in the Steam launch options like with Proton. E.g. `KAWARIKI_SDK=1 %command%`
See the runtime documentations for info.

### CLI
The CLI brings some options for non-Steam games and developers:

- `./kawariki run <path-to-game>` will try to run a game through Kawariki (As trough Steam Play)
- `./kawariki launcher <path-to-game> [filename]` Will create a launcher script in the game folder that runs the game trough Kawariki
<!--
- `./kawariki patch <path-to-game> -o <new-path>` Makes a copy of the game with it's engine replaced

Note: Patch mode doesn't (currently) support all features
-->

For more info see `./kawariki --help`


Runtimes
--------

Kawariki consists of a number of 'runtimes', each handling games
built with a specific set of common engines.

### NW.js

Games based on web technologies and bundled with the
[NW.js browser engine][nwjs].

This includes games based on, among others:
- RPGMaker MV
- RPGMaker MZ
- Tyrano Builder

[README][rt-nwjs]

### MKXP-Z

There is experimental support for RPGMaker games based on RGSS
using the [mkxp-z project][mkxp-z].

RPGMaker editions based on RGSS are:
- RPGMaker XP (RGSS1)
- RPGMaker VX (RGSS2)
- RPGMaker VX Ace (RGSS3)

[README][rt-mkxp]


overlayns-static
----------------

To avoid modifying the game installation, Linux namespaces are used
to 'overlay' the custom files over the install directory.

This requires unprivileged user namespaces to be enabled in the kernel
For example, In some versions of Ubuntu/Debian it can be enabled with
`sysctl -w kernel.unprivileged_userns_clone=1`

The overlayns binary works similarly to unshare(1) except it allows
mounts to be specified on the commandline.

Source: https://git.oro.sodimm.me/taeyeon/.files/src/branch/master/src/overlayns.cpp

License
-------

The code itself (kawariki) is GPL3+. Generated files like launcher scripts shall be CC0.
NW.js, Greenworks and Steamworks have their respective licenses.


<!-- References -->
[rt-nwjs]: nwjs/README.md
[rt-mkxp]: mkxp/README.md

[nwjs]: https://nwjs.io/
[mkxp-z]: https://roza-gb.gitbook.io/mkxp-z
