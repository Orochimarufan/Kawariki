import { String } from "$kawariki:es-polyfill";
import { Logger } from "./logger.mjs";
import { inject } from "./rpg-inject.mjs";
const logger = new Logger("RpgFixes", { color: 'MediumVioletRed' });
export const options = {
    line_wrap: false,
    line_max: 55,
};
inject.on("script-objects-loaded", () => {
    Game_Message.prototype.add = function (text) {
        while (options.line_wrap && text.length > options.line_max) {
            let snip = text.lastIndexOf(' ', options.line_max);
            if (snip < 10)
                snip = options.line_max;
            this._texts.push(text.slice(0, snip));
            text = text.slice(snip + 1);
        }
        this._texts.push(text);
    };
});
inject.on("boot", () => {
    const require = window.require;
    const path = require('path');
    const fs = require('fs');
    if (path.sep !== '\\' && StorageManager.localFileDirectoryPath !== undefined) {
        logger.info("Patching StorageManager to fix wrong directory separators");
        const sm = StorageManager;
        const _localFileDirPath = sm.localFileDirectoryPath;
        const _fixCache = {};
        if (String.includes(_localFileDirPath.toString(), '$dataSystem')) {
            logger.warn("BUG: StorageManager.localFileDirectoryPath() depends on $dataSystem and will cause loading of config to fail. Patching DataManager to load System.json synchronously");
            const _loadDataFile = DataManager.loadDataFile;
            DataManager.loadDataFile = function (name, src) {
                if (name === '$dataSystem') {
                    try {
                        const syspath = path.join(path.dirname(process.mainModule.filename), 'data', src);
                        const data = JSON.parse(fs.readFileSync(syspath));
                        window[name] = data;
                        DataManager.onLoad(data);
                        return;
                    }
                    catch (e) {
                        logger.error("Failed to load System.json synchronously", e);
                    }
                }
                return _loadDataFile.call(DataManager, name, src);
            };
        }
        sm.localFileDirectoryPath = function () {
            const p = _localFileDirPath.call(this);
            if (!String.includes(p, '\\'))
                return p;
            if (!_fixCache[p]) {
                try {
                    if (fs.existsSync(p)) {
                        logger.log("Fixing local storage path:", p);
                        const oldparent = path.dirname(p);
                        const oldprefix = path.basename(p);
                        const dirp = fs.opendirSync(oldparent);
                        let de;
                        while ((de = dirp.readSync()) !== null) {
                            if (de.isFile() && String.startsWith(de.name, oldprefix)) {
                                const newname = String.replaceAllLiteral(de.name, '\\', path.sep);
                                logger.log("Fixing local storage file: ", newname);
                                const newpath = path.join(oldparent, newname);
                                fs.mkdirSync(path.dirname(newpath), { recursive: true });
                                fs.renameSync(path.join(oldparent, de.name), newpath);
                            }
                        }
                        fs.rmdirSync(p);
                    }
                }
                catch (e) {
                    logger.error("Failed trying to fix local storage path:", p, e);
                }
                _fixCache[p] = true;
            }
            return String.replaceAllLiteral(p, '\\', path.sep);
        };
    }
    logger.info("Initialized");
});
//# sourceMappingURL=rpg-fixes.mjs.map