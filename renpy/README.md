Kawariki Ren'Py Runtime
=======================

[Ren'Py][renpy] is a [Python][python]-based Visual Novel engine. It uses a modified version of [PyGame][pygame] and games are typically implemented without native code. This allows running the game data files with a different SDK build even when no version for a platform is distributed.

### Running Games using a SDK
Ren'Py supports running any game export/project using a (compatible) Ren'Py SDK:

`renpy <path-to-game>`/`<path-to-sdk>/renpy.sh <path-to-game>`

This is also mentioned in the [official documentation][renpy-docs-runsdk].

Note that while there is some room for running games built with older versions with a newer SDK, changes across engine versions can quickly break things (Unlike with pure runtime replacement like NW.js)

### Ren'Py builds
Ren'Py exports multi-platform `pc` builds by default. Some developers explicitly select single-platform builds:

| Platform | Windows | Linux | MacOS |
| -------- | :-----: | :---: | :---: |
| `pc`     | Y | Y |     |
| `market` | Y | Y | (Y) |
| `win`    | Y |   |     |
| `linux`  |   | Y |     |
| `mac`    |   |   | Y   |

Ren'Py 8 and later are 64-bit only

[Documentation][renpy-docs-build]

### Version Detection
Kawariki needs to detect the version of Ren'Py a game is shipped with. It tries to extract this information from the runtime files (`renpy` and `lib/python*` in a game distribution). Therefore, while these files aren't used when actually running a game, they can't easily be removed (e.g. for saving space)


[renpy]: https://renpy.org/
[python]: https://python.org/
[pygame]: https://www.pygame.org
[renpy-docs-runsdk]: https://renpy.org/doc/html/raspi.html#running-a-game
[renpy-docs-build]: https://renpy.org/doc/html/build.html
