function extractPrototypeMethod(constr, name) {
    const fn = constr.prototype[name];
    return fn.call.bind(fn);
}
const _Object = globalThis.Object;
const _Array = globalThis.Array;
const _String = globalThis.String;
export const Object = {
    keys: _Object.keys,
    assign: _Object.assign,
    entries: _Object.entries,
    fromEntries: _Object.fromEntries,
    mapEntries(obj, fn) {
        return _Object.fromEntries(_Object.entries(obj).map(fn));
    },
};
export const Array = {
    flatMap: extractPrototypeMethod(_Array, "flatMap"),
    includes: extractPrototypeMethod(_Array, 'includes'),
    removeInPlace(arr, elm) {
        const ix = arr.indexOf(elm);
        if (ix >= 0)
            arr.splice(ix, 1);
    },
    unique(arr) {
        const newarr = [];
        for (const el of arr) {
            if (newarr.indexOf(el) < 0)
                newarr.push(el);
        }
        return newarr;
    },
};
export const String = {
    capitalize(string) {
        return string[0].toUpperCase() + string.slice(1);
    },
    endsWith: extractPrototypeMethod(_String, "endsWith"),
    includes: extractPrototypeMethod(_String, "includes"),
    replaceAllLiteral: extractPrototypeMethod(_String, "replaceAll"),
    startsWith: extractPrototypeMethod(_String, "startsWith"),
};
//# sourceMappingURL=es13-polyfill.mjs.map