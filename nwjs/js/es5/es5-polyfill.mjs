System.register([], function (exports_1, context_1) {
    "use strict";
    var _Object, _Array, _String, Object, Array, String;
    var __moduleName = context_1 && context_1.id;
    function extractPrototypeMethod(obj, name) {
        var fn = obj.prototype[name];
        return fn ? fn.call.bind(fn) : undefined;
    }
    return {
        setters: [],
        execute: function () {
            _Object = window.Object;
            _Array = window.Array;
            _String = window.String;
            exports_1("Object", Object = (function () {
                var _a, _b, _c;
                var keys = _Object.keys;
                var assign = ((_a = _Object.assign) !== null && _a !== void 0 ? _a : (function (target, source) {
                    keys(source).forEach(function (key) { return target[key] = source[key]; });
                    return target;
                }));
                var entries = ((_b = (_Object.entries)) !== null && _b !== void 0 ? _b : (function (obj) {
                    return keys(obj).map(function (k) { return [k, obj[k]]; });
                }));
                var fromEntries = ((_c = (_Object.fromEntries)) !== null && _c !== void 0 ? _c : (function (entries) {
                    var res = {};
                    for (var _i = 0, entries_1 = entries; _i < entries_1.length; _i++) {
                        var _a = entries_1[_i], k = _a[0], v = _a[1];
                        res[k] = v;
                    }
                    return res;
                }));
                var mapEntries = (_Object.fromEntries !== undefined
                    ? function (obj, fn) {
                        return fromEntries(entries(obj).map(fn));
                    }
                    : function (obj, fn) {
                        var newobj = {};
                        keys(obj).forEach(function (k) {
                            var entry = fn([k, obj[k]]);
                            newobj[entry[0]] = entry[1];
                        });
                        return newobj;
                    });
                return { assign: assign, entries: entries, fromEntries: fromEntries, keys: keys, mapEntries: mapEntries };
            })());
            exports_1("Array", Array = (function () {
                var _a;
                function flatMap(arr, fn) {
                    return _Array.prototype.concat.apply([], arr.map(fn));
                }
                var includes = ((_a = extractPrototypeMethod(_Array, 'includes')) !== null && _a !== void 0 ? _a : (function (arr, elem) { return arr.indexOf(elem) !== -1; }));
                function removeInPlace(arr, elm) {
                    var ix = arr.indexOf(elm);
                    if (ix >= 0)
                        arr.splice(ix, 1);
                }
                ;
                function unique(arr) {
                    var newarr = [];
                    for (var _i = 0, arr_1 = arr; _i < arr_1.length; _i++) {
                        var el = arr_1[_i];
                        if (newarr.indexOf(el) < 0)
                            newarr.push(el);
                    }
                    return newarr;
                }
                return { flatMap: flatMap, includes: includes, removeInPlace: removeInPlace, unique: unique };
            })());
            exports_1("String", String = (function () {
                var _a, _b, _c, _d;
                function capitalize(string) {
                    return string[0].toUpperCase() + string.slice(1);
                }
                var endsWith = ((_a = extractPrototypeMethod(_String, 'endsWith')) !== null && _a !== void 0 ? _a : (function (str, end, endp) {
                    endp !== null && endp !== void 0 ? endp : (endp = str.length);
                    return str.slice(endp - end.length, endp) == end;
                }));
                var includes = ((_b = extractPrototypeMethod(_String, 'includes')) !== null && _b !== void 0 ? _b : (function (str, ss) { return str.indexOf(ss) !== -1; }));
                var replaceAllLiteral = ((_c = extractPrototypeMethod(_String, 'replaceAll')) !== null && _c !== void 0 ? _c : (function (str, ss, repl) {
                    if (ss.length == 0)
                        throw new Error();
                    var ix = str.indexOf(ss);
                    var from = 0;
                    var parts = [];
                    while (ix > -1) {
                        var end = ix + ss.length;
                        parts.push(str.substring(from, end));
                        from = end;
                    }
                    if (from == 0)
                        return str;
                    parts.push(str.substring(from));
                    return parts.join(repl);
                }));
                var startsWith = ((_d = extractPrototypeMethod(_String, 'startsWith')) !== null && _d !== void 0 ? _d : (function (str, ss, startp) {
                    startp !== null && startp !== void 0 ? startp : (startp = 0);
                    return str.slice(startp, startp + ss.length) == ss;
                }));
                return { capitalize: capitalize, endsWith: endsWith, includes: includes, replaceAllLiteral: replaceAllLiteral, startsWith: startsWith };
            })());
        }
    };
});
//# sourceMappingURL=es5-polyfill.mjs.map