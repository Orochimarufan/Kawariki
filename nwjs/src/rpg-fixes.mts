// ==================================================================
// Fix some bugs
import { Object, Array, String } from "$kawariki:es-polyfill";
import { Logger } from "./logger.mjs";
import { inject } from "./rpg-inject.mjs";

const logger = new Logger("RpgFixes", {color: 'MediumVioletRed'});

export const options = {
    // Line wrapping
    line_wrap: false,   //< Enable forced line re-wrapping
    line_max: 55,       //< Wrap lines at column
};

inject.on("script-objects-loaded", () => {
    // Re-wrap lines
    // TODO: somehow compute rough wrapping point from font or something?
    Game_Message.prototype.add = function(this: Game_Message, text) {
        while (options.line_wrap && text.length > options.line_max) {
            let snip = text.lastIndexOf(' ', options.line_max);
            if (snip < 10)
                snip = options.line_max;
            this._texts.push(text.slice(0, snip));
            text = text.slice(snip+1);
        }
        this._texts.push(text);
    };
});

inject.on("boot", () => {
    const require = (window as any).require;
    const path = require('path');
    const fs = require('fs');
    // Fix path separator
    if (path.sep !== '\\' && (StorageManager as any).localFileDirectoryPath !== undefined) {
        logger.info("Patching StorageManager to fix wrong directory separators");
        const sm = StorageManager as any as _StorageManager;
        const _localFileDirPath = sm.localFileDirectoryPath;
        const _fixCache: Record<string, true> = {};
        if (String.includes(_localFileDirPath.toString(), '$dataSystem')) {
            // Must not depend on data, since data is loaded async
            // Have to patch to load data early or config load will fail
            logger.warn("BUG: StorageManager.localFileDirectoryPath() depends on $dataSystem and will cause loading of config to fail. Patching DataManager to load System.json synchronously");
            const _loadDataFile = DataManager.loadDataFile;
            DataManager.loadDataFile = function(name, src) {
                if (name === '$dataSystem') {
                    try {
                        const syspath = path.join(path.dirname(process.mainModule.filename), 'data', src);
                        const data = JSON.parse(fs.readFileSync(syspath));
                        (window as any)[name] = data;
                        DataManager.onLoad(data);
                        return;
                    } catch (e) {
                        logger.error("Failed to load System.json synchronously", e);
                    }
                }
                return _loadDataFile.call(DataManager, name, src);
            }
        }
        sm.localFileDirectoryPath = function() {
            const p: string = _localFileDirPath.call(this);
            if (!String.includes(p, '\\'))
                return p;
            if (!_fixCache[p]) {
                try {
                    if (fs.existsSync(p)) {
                        logger.log("Fixing local storage path:", p);
                        // Rename stuff
                        const oldparent = path.dirname(p);
                        const oldprefix = path.basename(p);
                        const dirp = fs.opendirSync(oldparent);
                        let de: any;
                        while ((de = dirp.readSync()) !== null) {
                            if (de.isFile() && String.startsWith(de.name, oldprefix)) {
                                const newname = String.replaceAllLiteral(de.name, '\\', path.sep);
                                logger.log("Fixing local storage file: ", newname);
                                const newpath = path.join(oldparent, newname);
                                fs.mkdirSync(path.dirname(newpath), {recursive: true});
                                fs.renameSync(path.join(oldparent, de.name), newpath);
                            }
                        }
                        fs.rmdirSync(p);
                    }
                } catch(e) {
                    logger.error("Failed trying to fix local storage path:", p, e);
                }
                _fixCache[p] = true;
            }
            return String.replaceAllLiteral(p, '\\', path.sep);
        }
    }
    logger.info("Initialized");
});
