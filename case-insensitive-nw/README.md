Case-Insensitive NW.js
======================

This directory contains a rudimentary script to allow NW.js apps that were written with only case-insensitive filesystems (like Windows) in mind to run from a case-sensitive file system: `case-insensitive-nw.js`.

Usage
-----

For now, it has to be manually included in the target app by copying it to `www/` and adding a Line to `www/index.html`, preferrably at the top of `<body>`:
```html
<script type="text/javascript" src="case-insensitive-nw.js"></script>
```

case-mismatches.json
--------------------

A file `case-mismatches.json` will be created in the app package directory when the first request with erroneous path casing is made by the app. It is used by `case-insensitive-nw.js` to cache lookup results and is useful for reporting the detected issues to the developer.
