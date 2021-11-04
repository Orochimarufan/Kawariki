(()=>{
    // Unfortunately, Chrome/NW.js WebRequest API is synchronous-only, unlike the Electron protocol API
    const fs = require('fs');
    const fsp = require('fs/promises');
    const path = require('path');
    const {URL} = require('url');

    const casemapFilename = "case-mismatches.json";
    let casemap = null;
    const loadCasemapFile = async(pathBase) => {
        const pathDb = path.join(pathBase, casemapFilename);
        if (await fsp.stat(pathDb).then(st=>true,err=>false)) {
            const jsonData = await fsp.readFile(pathDb);
            casemap = JSON.parse(jsonData);
        } else {
            casemap = {
                version: 1,
                note: "This file records instances where resources were accessed with filenames differing in case. "
                + "This is fine in case-folding/case-preserving environments like Windows or some macOS setups, "
                + "but it results in e.g. broken images on case-sensitive/opaque-path environments like Linux. "
                + "Records are listed in <path-that-was-specified>: <path-that-was-actually-found> format.",
                base: pathBase,
                record: {},
            };
        }
    };
    const saveCasemapFile = async(pathBase) => {
        const pathDb = path.join(pathBase, casemapFilename);
        await fsp.writeFile(pathDb, JSON.stringify(casemap, null, 2));
    };

    /**
     * Find a file in a directory using case-folding
     * @param {string} pathParent 
     * @param {string} name 
     * @param {boolean} wantDir 
     * @param {fs.Dir=} dirParent (always closed)
     * @returns string
     */
    const findFileNameCISync = (pathParent, name, wantDir, dirParent) => {
        // Always closes dirParent
        let dir = dirParent ?? fs.opendirSync(pathParent);
        // JS doesn't seem to have proper casefolding, so lowercase will have to do.
        const namel = name.toLowerCase();
        for (let ent = dir.readSync(); ent !== null; ent = dir.readSync()) {
            if (ent.name.toLowerCase() === namel && wantDir === ent.isDirectory()) {
                dir.closeSync();
                return ent.name;
            }
        };
        dir.closeSync();
        return null;
    };
    /**
     * @param {string} pathParent 
     * @param {string[]} pathElements 
     * @param {fs.Dir=} dirParent 
     * @returns string
     */
    const findFilePathCISync = (pathParent, pathElements, dirParent) => {
        const nameTentative = pathElements.shift();
        const pathTentative = path.join(pathParent, nameTentative);
        //console.log(">> Looking for", nameTentative, "in", pathParent);
        if (!pathElements.length) {
            // want file
            if (fs.existsSync(pathTentative)) {
                if (dirParent) dirParent.closeSync();
                    return pathTentative;
            } else {
                const nameResolved = findFileNameCISync(pathParent, nameTentative, false, dirParent);
                if (nameResolved) {
                    console.log("Miscased file name:", nameTentative, "in", pathParent, "is really", nameResolved);
                    return path.join(pathParent, nameResolved)
                }
                console.log("Could not find file:", nameTentative, "in", pathParent);
            }
        } else {
            // want directory
            try {
                const dir = fs.opendirSync(pathTentative);
                if (dirParent) dirParent.closeSync();
                return findFilePathCISync(pathTentative, pathElements, dir);
            } catch (e) {
                const nameResolved = findFilePathCISync(pathParent, nameTentative, true, dirParent);
                if (nameResolved) {
                    console.log("Miscased directory name:", nameTentative, "in", pathParent, "is really", nameResolved);
                    return findFilePathCISync(path.join(pathParent, nameResolved), pathElements);
                }
                console.log("Could not find directory:", nameTentative, "in", pathParent);
            }
        }
    };

    loadCasemapFile(".").then(() => {
        chrome.webRequest.onBeforeRequest.addListener(details => {
            const url = new URL(details.url);
            const relPath = url.pathname.substring(1);
            if (!fs.existsSync(relPath)) {
                if (casemap.record.hasOwnProperty(relPath)) {
                    const pathCached = casemap.record[relPath];
                    if (fs.existsSync(pathCached)) {
                        return {redirectUrl: chrome.runtime.getURL(pathCached)};
                    }
                } else {
                    const pathFound = (() => {
                        try {
                            return findFilePathCISync(".", relPath.split('/'));
                        } catch (e) {
                            return null;
                        }
                    })();
                    casemap.record[relPath] = pathFound;
                    saveCasemapFile(".").catch(console.error);
                    if (pathFound) {
                        return {redirectUrl: chrome.runtime.getURL(pathFound)};
                    }
                }
            }
            return {};
        },
        {urls:[chrome.runtime.getURL("/*")]}, ["blocking"]);
    });

    window._casein = {loadCasemapFile, saveCasemapFile, findFilePathCISync, findFileNameCISync, get casemap() { return casemap; }};
})();
