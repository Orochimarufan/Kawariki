System.register(["./logger.mjs", "$kawariki:es-polyfill", "./scriptobserver.mjs"], function (exports_1, context_1) {
    "use strict";
    var logger_mjs_1, _kawariki_es_polyfill_1, scriptobserver_mjs_1, Injector, inject;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (logger_mjs_1_1) {
                logger_mjs_1 = logger_mjs_1_1;
            },
            function (_kawariki_es_polyfill_1_1) {
                _kawariki_es_polyfill_1 = _kawariki_es_polyfill_1_1;
            },
            function (scriptobserver_mjs_1_1) {
                scriptobserver_mjs_1 = scriptobserver_mjs_1_1;
            }
        ],
        execute: function () {
            Injector = (function () {
                function Injector(observer) {
                    var _this = this;
                    this.logger = new logger_mjs_1.Logger("RpgInject", { color: "MediumPurple" });
                    this.log_event = this.logger.makeLogFn('debug', 'Triggered %s: %o');
                    this.listeners = {};
                    var se = Injector.scriptEventName;
                    this.scripts = Injector.defaultScripts.concat();
                    this.events = Injector.fixedEvents.concat(_kawariki_es_polyfill_1.Array.flatMap(_kawariki_es_polyfill_1.Array.unique(this.scripts.map(function (_a) {
                        var _ = _a[0], k = _a[1];
                        return k;
                    })), function (name) { return [se(name, 'added'), se(name, 'loaded')]; }));
                    this.observer = observer;
                    this.observer.on('add', function (_, script) {
                        var detail = { script: script };
                        var events_added = ['script-added'];
                        var events_loaded = ['script-loaded'];
                        if (script.src !== '') {
                            var src = new URL(script.src);
                            for (var _i = 0, _a = _this.scripts; _i < _a.length; _i++) {
                                var _b = _a[_i], scriptname = _b[0], eventname = _b[1];
                                if (_kawariki_es_polyfill_1.String.endsWith(src.pathname, scriptname)) {
                                    events_added.push(se(eventname, 'added'));
                                    events_loaded.push(se(eventname, 'loaded'));
                                }
                            }
                        }
                        _this.dispatch(events_added, detail);
                        script.addEventListener('load', _this.dispatch.bind(_this, events_loaded, detail));
                    });
                    this.on('script-managers-loaded', function (detail) {
                        var self = _this;
                        var isMV = Utils.RPGMAKER_NAME === "MV";
                        var extractFileName = Utils.RPGMAKER_NAME === "MZ" && Utils.extractFileName !== undefined
                            ? Utils.extractFileName.bind(Utils)
                            : function (name) { return name; };
                        PluginManager.setup = function (plugins) {
                            self.dispatch(['plugins-setup'], { plugins: plugins });
                            for (var _i = 0, plugins_1 = plugins; _i < plugins_1.length; _i++) {
                                var plugin = plugins_1[_i];
                                var key = plugin._filename = extractFileName(plugin.name);
                                if (plugin.status && !_kawariki_es_polyfill_1.Array.includes(this._scripts, key)) {
                                    self.dispatch(['plugin-setup'], { plugin: plugin });
                                    this.setParameters(key, plugin.parameters);
                                    this.loadScript(isMV ? plugin.name + ".js" : plugin.name);
                                    this._scripts.push(key);
                                    self.dispatch(['plugin-loaded'], { plugin: plugin });
                                }
                            }
                            self.dispatch(['plugins-loaded'], { plugins: plugins });
                        };
                    });
                    this.on('plugins-loaded', function (detail) {
                        var _run = SceneManager.run;
                        var self = _this;
                        SceneManager.run = function (scene) {
                            self.dispatch(['boot'], {});
                            _run.call(this, scene);
                        };
                    });
                    var timeout;
                    var timeoutcb = function () {
                        var msg = "Timed out trying to inject Kawariki plugins. Reloading with F5 may help.";
                        _this.logger.warn(msg);
                        alert(msg);
                        timeout = null;
                    };
                    timeout = window.setTimeout(timeoutcb, 3000);
                    this.on('plugins-setup', function () {
                        window.clearTimeout(timeout);
                        timeout = window.setTimeout(timeoutcb, 30000);
                    });
                    this.on('boot', function () {
                        window.clearTimeout(timeout);
                        timeout = null;
                        _this.logger.info("RPGMaker game booted successfully");
                    });
                }
                Injector.prototype.dispatch = function (names, detail) {
                    var _a, _b;
                    var prefix = (_a = names[0]) === null || _a === void 0 ? void 0 : _a.slice(0, 7);
                    if (names.length !== 1 || (prefix !== 'script-' && prefix !== 'plugin-'))
                        this.log_event(names, detail);
                    for (var _i = 0, names_1 = names; _i < names_1.length; _i++) {
                        var name_1 = names_1[_i];
                        for (var _c = 0, _d = (_b = this.listeners[name_1]) !== null && _b !== void 0 ? _b : []; _c < _d.length; _c++) {
                            var lner = _d[_c];
                            lner(detail, this);
                        }
                    }
                };
                Injector.scriptEventName = function (scriptname, type) {
                    return "script-".concat(scriptname, "-").concat(type);
                };
                Object.defineProperty(Injector.prototype, "eventNames", {
                    get: function () {
                        return this.events;
                    },
                    enumerable: false,
                    configurable: true
                });
                Injector.prototype.observeScript = function (scriptsrc, eventprefix) {
                    this.scripts.push([scriptsrc, eventprefix]);
                    var events = [Injector.scriptEventName(eventprefix, 'added'), Injector.scriptEventName(eventprefix, 'loaded')];
                    this.events.push.apply(this.events, events);
                    return events;
                };
                Injector.prototype.on = function (type, callback) {
                    var lners = this.listeners[type];
                    if (lners === undefined)
                        this.listeners[type] = [callback];
                    else
                        lners.push(callback);
                };
                Injector.defaultScripts = [
                    ['js/plugins.js', 'plugins'],
                    ['js/main.js', 'main'],
                    ['js/rpg_core.js', 'core'],
                    ['js/rpg_managers.js', 'managers'],
                    ['js/rpg_objects.js', 'objects'],
                    ['js/rmmz_core.js', 'core'],
                    ['js/rmmz_managers.js', 'managers'],
                    ['js/rmmz_objects.js', 'objects'],
                ];
                Injector.fixedEvents = [
                    'script-added',
                    'script-loaded',
                    'plugins-setup',
                    'plugins-loaded',
                    'plugin-setup',
                    'plugin-loaded',
                    'boot',
                ];
                return Injector;
            }());
            exports_1("Injector", Injector);
            exports_1("inject", inject = new Injector(scriptobserver_mjs_1.global()));
        }
    };
});
//# sourceMappingURL=rpg-inject.mjs.map