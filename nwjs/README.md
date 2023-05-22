Kawariki NW.js runtime
======================

NW.js based games were the original target for Kawariki.
Support for patching Greenworks natives is included.

Links: [Project Website][nwjs]


Notable engines based on NW.js
------------------------------

### RPGMaker MV and MZ

While RPGMaker MV supports (for the first time ever) exporting
to Linux, many developers do not use this option and some report
issues with it. This option also seems to be missing in MZ.

Both engines are based on an unmodified NW.js runtime and
it is a viable strategy to run Windows exports on
a native runtime procured directly from the NW.js project.
Special care must be taken with regards to plugins depending
on native code (like Greenworks).

Links: [Official Website][rpgmakerweb], [MV Steam][steam-rmmv]

### Tyrano Builder

Games made using Tyrano Builder/TyranoScript are based on NW.js as well.

The engine is not written with Linux support in mind at all, though
Android is natively supported. As such, there are relatively few
issues running on Linux.
A fix for the Linux-specific [Issue #87][tyrano-issue87] is automatically
applied if a Tyrano-based game is identified.

Note that a lot Tyrano-based games come with all code and assets
packaged in their main executable (i.e. the Windows `.exe`).
See also the `Special Considerations` section below.

Links: [Official Website][tyrano], [GitHub][tyrano-github]


Special Considerations
----------------------

### Packaged Apps

NW.js apps may be [packaged as a ZIP archive][nwjs-packaing].
Such apps are supported, but must be unpacked to /tmp
by the runtime before actually running them.

Please note that any changes the app makes to it's directory
(for example, RPGMaker MV/MZ store savegames in the app directory)
are discarded when the app exits. As such, the app must be designed
with such a setup in mind.

### Greenworks

Some support is included for Greenworks (NW.js Steamworks library).
This is achieved by trying to replace the game's greenworks library
with one that includes the correct linux native modules.

This uses `overlayns-static` (see [main readme][readme])

For Greenworks to be supported with a given NW.js version,
the corresponding native binaries must exist in
the `greenworks/` directory and be referred in `versions.json`.

The required files can be gotten from the relevant Steam Partner pages
and https://greenworks-prebuilds.armaldio.xyz/ or built from source.


Injected Plugins
----------------

Custom code can be injected into the game.
See the [injects readme][injects].

This (currently) requires `overlayns-static` support
(see the [main readme][readme]) to shadow the game's package.json.

Custom user-scripts can be added to a game's root directory and will
be injected when named `*.kawariki.js`

#### Filesystem case-sensitivity

A plugin to handle case-insensitive file lookups (`case-insensitive-nw.js`)
is automatically injected into NW.js games launched through Kawariki.


Configuration
-------------

### Environment Variables
- `KAWARIKI_SDK=1` Use NW.js with DevTools support
- `KAWARIKI_NWJS=<name>` Use a specific NW.js version
- `KAWARIKI_NO_UNPACK=1` Don't allow unpacking packaged apps to /tmp
- `KAWARIKI_NO_OVERLAYNS=1` Disallow usage of overlayns-static
- `KAWARIKI_NWJS_DEVTOOLS=1` Try to open DevTools on startup
- `KAWARIKI_NWJS_CIFS=1` Replace Node.js filesystem interfaces with case-insensitive versions
- `KAWARIKI_NWJS_INJECT_BG=1` Inject all scripts into the content instead of the background context (Useful for debugging via DevTools)
- `KAWARIKI_NWJS_IGNORE_LEGACY_MV=1` Don't try to use old Nw.js with RPGMaker MV versions older than 1.6

### versions.json

This file specifies the NW.js versions that should be considered.
Available keys are:
- `version` *required array-of-numbers* The NW.js version of this distribution (e.g. `[0,54,1]`)
- `dist` *required string* The name of the directory the distribution is stored in.
- `dist_url` *string* An URL to download the distribution from if not already available. It must point to a gzip/bzip2/xz compressed tar-archive.
- `name` *string* An optional name given to the distribution for use with `--nwjs`. Defaults to the value of `dist`.
- `sdk` *boolean* Wether the distribution is a SDK release (i.e. includes DevTools). Defaults to `false`.
- `greenworks` *string* Name of a directory containing compatible replacements for the greenworks library. Greenworks is not supported if omitted.

By default, the most recent installed NW.js distribution is chosen,
or the very latest is downloaded if none is available.
All downloads occur to the `dist/` subdirectory.


<!-- References -->
[readme]: ../README.md
[injects]: injects/README.md

[nwjs]: https://nwjs.io/
[nwjs-packaing]: https://docs.nwjs.io/en/latest/For%20Users/Package%20and%20Distribute/#package-option-2-zip-file

[rpgmakerweb]: https://www.rpgmakerweb.com/
[steam-rmmv]: https://store.steampowered.com/app/363890/RPG_Maker_MV/

[tyrano]: https://tyrano.jp/
[tyrano-github]: https://github.com/ShikemokuMK/tyranoscript
[tyrano-issue87]: https://github.com/ShikemokuMK/tyranoscript/issues/87
