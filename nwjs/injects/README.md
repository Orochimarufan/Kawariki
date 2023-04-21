NW.js game modifications
========================

This directory contains scripts that can be injected into NW.js games to extend functionality or workaround platform assumptions.


case-insensitive-nw.js
----------------------

Provides a WebRequest handler that tries to look up missing files case-insensitively. Very useful for games exclusively developed on Windows.

### case-mismatches.json

A file `case-mismatches.json` will be created in the app package directory when the first request with erroneous path casing is made by the app. It is used to cache lookup results and is useful for reporting the detected issues to the developer.


rpg-remap.js
------------

Experimental and WIP modification to allow rebinding keys in RPGMaker MV/MZ games that don't natively support it.

Currently, it always injects a default mapping:
| Key | | Key |             |
| - | - | - | ------------- |
| W | ↑ | E | Confirm       |
| A | ← | Q | Cancel/Menu   |
| S | ↓ |   |               |
| D | → |   |               |

It also provides a Console API:
```js
Remap.initial       // The game's initial keymap
Remap.map           // Configured keymap
Remap.get()         // Get the currently active keymap
Remap.apply()       // Apply the configured keymap
Remap.set(key, act) // Set a key mapping
Remap.add(map)      // Add multiple key mappings
```


rpg-vars.js
-----------

Utilities for inspecting RPGMaker MV/MZ variables and switches.

You can get a list of Variables (and/or switches) using these methods:
```js
RpgVariable.allVariables()
RpgVariable.allSwitches()
RpgVariable.findName(name)
RpgVariable.findValue(x)
```

The returned is an array with additional methods for narrowing down the selectron:
```js
vars.narrow(f)          // By filter function
vars.narrowChanged()    // Keep only recently changed variables
vars.narrowValue(x)     // By current (possibly changed) value
vars.slice()            // You can get a (shallow) copy using slice()
```

RpgVariable objects have the following methods:
```js
v.get()             // Get the current value
v.set(x)            // Set a new value
v.hasChanged()      // Check if it changed
v.pollChanged()     // Check if it changed without resetting changed-ness
```


mv-decrypted-assets.js, mz-decrypted-assets.js
----------------------------------------------

These scripts modify RPGMaker MV/MZ games to be able to load decrypted assets even when System.json indicates they should be encrypted.
This is useful e.g. when wanting to mod a game without having to encrypt the modded assets or for sharing assets on disk between different games and/or different versions of a game.

They must be enabled using the environment variable `KAWARIKI_NWJS_RPG_DECRYPTED_ASSETS=1`

> ⓘ Fully decrypted games can run without this given the appropriate modifications to `(www/)data/System.json`
>
> Also note that this deals only with standard RPGMaker MV/MZ asset encryption (.rpgmvo, .ogg_, etc), not any additional custom protections a game might implement.
