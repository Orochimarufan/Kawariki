System.register(["$kawariki:es-polyfill", "./logger.mjs", "./rpg-inject.mjs"], function (exports_1, context_1) {
    "use strict";
    var _kawariki_es_polyfill_1, logger_mjs_1, rpg_inject_mjs_1, logger, options;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (_kawariki_es_polyfill_1_1) {
                _kawariki_es_polyfill_1 = _kawariki_es_polyfill_1_1;
            },
            function (logger_mjs_1_1) {
                logger_mjs_1 = logger_mjs_1_1;
            },
            function (rpg_inject_mjs_1_1) {
                rpg_inject_mjs_1 = rpg_inject_mjs_1_1;
            }
        ],
        execute: function () {
            logger = new logger_mjs_1.Logger("RpgFixes", { color: 'MediumVioletRed' });
            exports_1("options", options = {
                line_wrap: false,
                line_max: 55,
            });
            rpg_inject_mjs_1.inject.on("script-objects-loaded", function () {
                Game_Message.prototype.add = function (text) {
                    while (options.line_wrap && text.length > options.line_max) {
                        var snip = text.lastIndexOf(' ', options.line_max);
                        if (snip < 10)
                            snip = options.line_max;
                        this._texts.push(text.slice(0, snip));
                        text = text.slice(snip + 1);
                    }
                    this._texts.push(text);
                };
            });
            rpg_inject_mjs_1.inject.on("boot", function () {
                var require = window.require;
                var path = require('path');
                var fs = require('fs');
                if (path.sep !== '\\' && StorageManager.localFileDirectoryPath !== undefined) {
                    logger.info("Patching StorageManager to fix wrong directory separators");
                    var sm = StorageManager;
                    var _localFileDirPath_1 = sm.localFileDirectoryPath;
                    var _fixCache_1 = {};
                    if (_kawariki_es_polyfill_1.String.includes(_localFileDirPath_1.toString(), '$dataSystem')) {
                        logger.warn("BUG: StorageManager.localFileDirectoryPath() depends on $dataSystem and will cause loading of config to fail. Patching DataManager to load System.json synchronously");
                        var _loadDataFile_1 = DataManager.loadDataFile;
                        DataManager.loadDataFile = function (name, src) {
                            if (name === '$dataSystem') {
                                try {
                                    var syspath = path.join(path.dirname(process.mainModule.filename), 'data', src);
                                    var data = JSON.parse(fs.readFileSync(syspath));
                                    window[name] = data;
                                    DataManager.onLoad(data);
                                    return;
                                }
                                catch (e) {
                                    logger.error("Failed to load System.json synchronously", e);
                                }
                            }
                            return _loadDataFile_1.call(DataManager, name, src);
                        };
                    }
                    sm.localFileDirectoryPath = function () {
                        var p = _localFileDirPath_1.call(this);
                        if (!_kawariki_es_polyfill_1.String.includes(p, '\\'))
                            return p;
                        if (!_fixCache_1[p]) {
                            try {
                                if (fs.existsSync(p)) {
                                    logger.log("Fixing local storage path:", p);
                                    var oldparent = path.dirname(p);
                                    var oldprefix = path.basename(p);
                                    var dirp = fs.opendirSync(oldparent);
                                    var de = void 0;
                                    while ((de = dirp.readSync()) !== null) {
                                        if (de.isFile() && _kawariki_es_polyfill_1.String.startsWith(de.name, oldprefix)) {
                                            var newname = _kawariki_es_polyfill_1.String.replaceAllLiteral(de.name, '\\', path.sep);
                                            logger.log("Fixing local storage file: ", newname);
                                            var newpath = path.join(oldparent, newname);
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
                            _fixCache_1[p] = true;
                        }
                        return _kawariki_es_polyfill_1.String.replaceAllLiteral(p, '\\', path.sep);
                    };
                }
                logger.info("Initialized");
            });
        }
    };
});
//# sourceMappingURL=rpg-fixes.mjs.map