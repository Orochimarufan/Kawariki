System.register(["./logger.mjs", "$kawariki:es-polyfill"], function (exports_1, context_1) {
    "use strict";
    var logger_mjs_1, _kawariki_es_polyfill_1, Injector, inject;
    var __moduleName = context_1 && context_1.id;
    function isElement(node) {
        return node.nodeType === node.ELEMENT_NODE;
    }
    function isScriptElement(node) {
        return isElement(node) && node.tagName === "SCRIPT";
    }
    return {
        setters: [
            function (logger_mjs_1_1) {
                logger_mjs_1 = logger_mjs_1_1;
            },
            function (_kawariki_es_polyfill_1_1) {
                _kawariki_es_polyfill_1 = _kawariki_es_polyfill_1_1;
            }
        ],
        execute: function () {
            Injector = (function () {
                function Injector() {
                    var _this = this;
                    this.logger = new logger_mjs_1.Logger("RpgInject", { color: "MediumPurple" });
                    this.log_event = this.logger.makeLogFn('info', 'Triggered %s: %o');
                    this.listeners = {};
                    var se = Injector.scriptEventName;
                    this.scripts = Injector.defaultScripts.concat();
                    this.events = Injector.fixedEvents.concat(_kawariki_es_polyfill_1.Array.flatMap(_kawariki_es_polyfill_1.Array.unique(this.scripts.map(function (_a) {
                        var _ = _a[0], k = _a[1];
                        return k;
                    })), function (name) { return [se(name, 'added'), se(name, 'loaded')]; }));
                    this.observer = new MutationObserver(function (mutations) {
                        for (var _i = 0, mutations_1 = mutations; _i < mutations_1.length; _i++) {
                            var m = mutations_1[_i];
                            m.addedNodes.forEach(function (e) {
                                if (isScriptElement(e)) {
                                    var detail = { script: e };
                                    var events_added = ['script-added'];
                                    var events_loaded = ['script-loaded'];
                                    if (e.src !== '') {
                                        var src = new URL(e.src);
                                        for (var _i = 0, _a = _this.scripts; _i < _a.length; _i++) {
                                            var _b = _a[_i], scriptname = _b[0], eventname = _b[1];
                                            if (_kawariki_es_polyfill_1.String.endsWith(src.pathname, scriptname)) {
                                                events_added.push(se(eventname, 'added'));
                                                events_loaded.push(se(eventname, 'loaded'));
                                            }
                                        }
                                    }
                                    _this.dispatch(events_added, detail);
                                    e.addEventListener('load', _this.dispatch.bind(_this, events_loaded, detail));
                                }
                            });
                        }
                    });
                    document.addEventListener("DOMContentLoaded", this.observer.disconnect.bind(this.observer));
                    this.observer.observe(document, {
                        childList: true,
                        subtree: true,
                    });
                    this.on('script-managers-loaded', function (detail) {
                        var self = _this;
                        var extractFileName = Utils.RPGMAKER_NAME === "MV"
                            ? function (name) { return name + ".js"; }
                            : Utils.extractFileName !== undefined
                                ? Utils.extractFileName.bind(Utils)
                                : function (name) { return name; };
                        PluginManager.setup = function (plugins) {
                            self.dispatch(['plugins-setup'], { plugins: plugins });
                            for (var _i = 0, plugins_1 = plugins; _i < plugins_1.length; _i++) {
                                var plugin = plugins_1[_i];
                                if (plugin.status && !_kawariki_es_polyfill_1.Array.includes(this._scripts, plugin.name)) {
                                    plugin._filename = extractFileName(plugin.name);
                                    self.dispatch(['plugin-setup'], { plugin: plugin });
                                    this.setParameters(plugin.name, plugin.parameters);
                                    this.loadScript(plugin._filename);
                                    this._scripts.push(plugin.name);
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
                    ['js/rmmz_core.js', 'core'],
                    ['js/rmmz_managers.js', 'managers'],
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
            exports_1("inject", inject = new Injector());
        }
    };
});
//# sourceMappingURL=rpg-inject.mjs.map