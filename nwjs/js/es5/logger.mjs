System.register([], function (exports_1, context_1) {
    "use strict";
    var Logger;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [],
        execute: function () {
            Logger = (function () {
                function Logger(name, options) {
                    var _a, _b;
                    this.name = name;
                    this.color = (_a = options === null || options === void 0 ? void 0 : options.color) !== null && _a !== void 0 ? _a : Logger.DEFAULT_COLORS[(this.idhash & 0xFFFF) % Logger.DEFAULT_COLORS.length];
                    this.console = (_b = options === null || options === void 0 ? void 0 : options.console) !== null && _b !== void 0 ? _b : window.console;
                }
                Object.defineProperty(Logger.prototype, "idhash", {
                    get: function () {
                        var s = this.name;
                        for (var i = 0, h = 9; i < s.length;)
                            h = Math.imul(h ^ s.charCodeAt(i++), Math.pow(9, 9));
                        return h ^ h >>> 9;
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(Logger.prototype, "prefix_fmt", {
                    get: function () {
                        return '%c%s%c';
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(Logger.prototype, "prefix_fparams", {
                    get: function () {
                        return [
                            "background-color: ".concat(this.color, "; color: white; padding: 0.1rem 0.25rem; border-radius: 4px;"),
                            this.name,
                            "background-color: default; color: default; padding: default; border-radius: 0;"
                        ];
                    },
                    enumerable: false,
                    configurable: true
                });
                Logger.prototype.makeLogFn = function (level, fmt) {
                    var data = [];
                    for (var _i = 2; _i < arguments.length; _i++) {
                        data[_i - 2] = arguments[_i];
                    }
                    var fn = this.console[level];
                    var xfmt = fmt ? "".concat(this.prefix_fmt, " ").concat(fmt) : this.prefix_fmt;
                    return fn.bind.apply(fn, [this.console, xfmt].concat(this.prefix_fparams, data));
                };
                Logger.prototype.makeMemoFn = function (level) {
                    var fn = this.makeLogFn(level);
                    Object.defineProperty(this, level, { value: fn });
                    return fn;
                };
                Object.defineProperty(Logger.prototype, "log", {
                    get: function () {
                        return this.makeMemoFn('log');
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(Logger.prototype, "debug", {
                    get: function () {
                        return this.makeMemoFn('debug');
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(Logger.prototype, "trace", {
                    get: function () {
                        return this.makeMemoFn('trace');
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(Logger.prototype, "info", {
                    get: function () {
                        return this.makeMemoFn('info');
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(Logger.prototype, "warn", {
                    get: function () {
                        return this.makeMemoFn('warn');
                    },
                    enumerable: false,
                    configurable: true
                });
                Object.defineProperty(Logger.prototype, "error", {
                    get: function () {
                        return this.makeMemoFn('error');
                    },
                    enumerable: false,
                    configurable: true
                });
                Logger.DEFAULT_COLORS = [
                    "maroon", "purple", "fuchsia", "green", "lime", "olive", "navy", "blue", "teal", "aqua",
                    "aquamarine", "bisque", "blueviolet", "brown", "cadetblue", "chocolate", "coral", "cornflowerblue", "crimson",
                    "darkblue", "darkcyan", "darkgoldenrod", "darkgrey", "darkgreen", "darkkhaki", "darkmagenta", "darkolivegreen", "darkorchid",
                    "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategrey", "darkviolet", "deeppink", "deepskyblue",
                    "dodgerblue", "firebrick", "forestgreen", "fuchsia", "hotpink", "indianred", "indigo", "limegreen",
                    "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen",
                    "mediumturquoise", "mediumvioletred", "midnightblue", "olive", "orange", "orangered", "orchid", "plum", "rebeccapurple",
                    "royalblue", "saddlebrown", "seagreen", "sienna", "slateblue", "steelblue", "tomato"
                ];
                return Logger;
            }());
            exports_1("Logger", Logger);
        }
    };
});
//# sourceMappingURL=logger.mjs.map