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


### Live2D Cubism
For games using [Live2D Cubism][live2d], the proprietary Live2D SDK needs to be installed. This can be done as described in the [Ren'Py Documentation][renpy-docs-live2d]. The correct Ren'Py SDK Launcher can be started using `kawariki run --renpy-launcher <path-to-game-exe>`.

[renpy]: https://renpy.org/
[python]: https://python.org/
[pygame]: https://www.pygame.org
[live2d]: https://www.live2d.com/en/
[renpy-docs-runsdk]: https://renpy.org/doc/html/raspi.html#running-a-game
[renpy-docs-build]: https://renpy.org/doc/html/build.html
[renpy-docs-live2d]: https://www.renpy.org/doc/html/live2d.html
