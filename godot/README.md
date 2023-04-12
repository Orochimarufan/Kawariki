Kawariki Godot Runtime
======================

It is possible for (some?) Godot games to run unmodified using an [official linux build][godot-downloads]. This runtime  tries to run a game's `.pck` pack-file using `--main-pack`.

This is still very experimental and not very well tested:
- The detection logic is not very smart yet, so the original filename must be included in the kawariki command
- Games that have all their resources bundled into the executable are not supported yet
- Detection of the engine version is not implemented yet, so only 3.5.2 is currently supported


[godot-downloads]: https://godotengine.org/download/linux/
