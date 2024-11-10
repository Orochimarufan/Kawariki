System.register([], function (exports_1, context_1) {
    "use strict";
    var ScriptObserver, GLOBAL;
    var __moduleName = context_1 && context_1.id;
    function global() {
        if (GLOBAL === null) {
            GLOBAL = new ScriptObserver();
            GLOBAL.observe();
        }
        return GLOBAL;
    }
    exports_1("global", global);
    return {
        setters: [],
        execute: function () {
            ScriptObserver = (function () {
                function ScriptObserver() {
                    var _this = this;
                    this._active = false;
                    this._pending = 0;
                    this._errors = 0;
                    this._count = 0;
                    this._listeners = { "add": [], "load": [], "error": [], "settled": [] };
                    this._observer = new MutationObserver(function (mutations) {
                        for (var _i = 0, mutations_1 = mutations; _i < mutations_1.length; _i++) {
                            var m = mutations_1[_i];
                            m.addedNodes.forEach(function (e) {
                                if (e.nodeName === "SCRIPT") {
                                    _this._dispatch(e, "add");
                                    e.addEventListener("load", _this._dispatch.bind(_this, e, "load"));
                                    e.addEventListener("error", _this._dispatch.bind(_this, e, "error"));
                                }
                            });
                        }
                    });
                }
                ScriptObserver.prototype._dispatch = function (script, event) {
                    if (event === "add") {
                        this._pending += 1;
                        this._count += 1;
                    }
                    else {
                        this._pending -= 1;
                        if (event === "error")
                            this._errors += 1;
                    }
                    for (var _i = 0, _a = this._listeners[event]; _i < _a.length; _i++) {
                        var l = _a[_i];
                        l(event, script);
                    }
                    if (this._pending < 1) {
                        for (var _b = 0, _c = this._listeners.settled; _b < _c.length; _b++) {
                            var l = _c[_b];
                            l("settled");
                        }
                    }
                };
                ScriptObserver.prototype.observe = function () {
                    this._active = true;
                    this._pending = 0;
                    this._errors = 0;
                    this._count = 0;
                    this._observer.observe(document, {
                        childList: true,
                        subtree: true,
                    });
                };
                ScriptObserver.prototype.disconnect = function () {
                    this._observer.disconnect();
                    this._active = false;
                };
                ScriptObserver.prototype.on = function (events, listener) {
                    if (!Array.isArray(events))
                        events = [events];
                    for (var _i = 0, events_1 = events; _i < events_1.length; _i++) {
                        var event_1 = events_1[_i];
                        this._listeners[event_1].push(listener);
                    }
                    return listener;
                };
                ScriptObserver.prototype.off = function (events, listener) {
                    if (events === null)
                        events = ["add", "error", "load", "settled"];
                    else if (!Array.isArray(events))
                        events = [events];
                    for (var _i = 0, events_2 = events; _i < events_2.length; _i++) {
                        var event_2 = events_2[_i];
                        var i = this._listeners[event_2].indexOf(listener);
                        if (i >= 0)
                            this._listeners[event_2].splice(i, 1);
                    }
                };
                Object.defineProperty(ScriptObserver.prototype, "pending", {
                    get: function () {
                        return this._pending;
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(ScriptObserver.prototype, "errors", {
                    get: function () {
                        return this._errors;
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(ScriptObserver.prototype, "count", {
                    get: function () {
                        return this._count;
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(ScriptObserver.prototype, "active", {
                    get: function () {
                        return this._active;
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(ScriptObserver.prototype, "settled", {
                    get: function () {
                        return this._pending < 1;
                    },
                    enumerable: false,
                    configurable: true
                });
                return ScriptObserver;
            }());
            exports_1("ScriptObserver", ScriptObserver);
            GLOBAL = null;
        }
    };
});
//# sourceMappingURL=scriptobserver.mjs.map