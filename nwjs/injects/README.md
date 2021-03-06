NW.js game modifications
========================

This directory contains scripts that can be injected into NW.js games to extend functionality or workaround platform assumptions.


case-insensitive-nw.js
----------------------

Provides a WebRequest handler that tries to look up missing files case-insensitively. Very useful for games exclusively developed on Windows.

### case-mismatches.json

A file `case-mismatches.json` will be created in the app package directory when the first request with erroneous path casing is made by the app. It is used to cache lookup results and is useful for reporting the detected issues to the developer.


remap-mv.js
-----------

Experimental and WIP modification to allow rebinding keys in RPGMaker MV games that don't natively support it.


mv-decrypted-assets.js
----------------------

This script modifies RPGMaker MV games to be able to load decrypted assets even when System.json indicates they should be encrypted.
This is useful e.g. when wanting to mod a game without having to encrypt the modded assets or for sharing assets on disk between different games and/or different versions of a game.
