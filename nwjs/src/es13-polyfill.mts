import type { ArrayUtils, EntryMapFn, ObjectUtils, StringUtils } from "./es-polyfill.d.mts";

type ExplicitThis<T, Fn extends (this: T, ...args: any[]) => any> = Fn extends (this: T, ...args: infer Args) => infer R ? (self: T, ...args: Args) => R : never;
function extractPrototypeMethod<C extends abstract new (...args: any) => any, N extends keyof InstanceType<C>>(constr: C, name: N): ExplicitThis<InstanceType<C>, InstanceType<C>[N]> {
    const fn = constr.prototype[name];
    return fn.call.bind(fn);
}

const _Object = globalThis.Object;
const _Array = globalThis.Array;
const _String = globalThis.String;

export const Object: ObjectUtils = {
    keys: _Object.keys,
    assign: _Object.assign,
    entries: _Object.entries,
    fromEntries: _Object.fromEntries,
    mapEntries<K extends string|number|symbol, V, RK extends string|number|symbol, RV>(obj: Record<K,V>, fn: EntryMapFn<K,V,RK,RV>) {
        return _Object.fromEntries(_Object.entries(obj).map(fn as ([string, V])=>[string, RV])) as Record<RK, RV>;
    },
};

export const Array: ArrayUtils = {
    // type parameters get turned into unknown by extractPrototypeMethod
    flatMap: extractPrototypeMethod(_Array, "flatMap") as ArrayUtils["flatMap"],
    includes: extractPrototypeMethod(_Array, 'includes') as ArrayUtils["includes"],
    removeInPlace<T>(arr: T[], elm: T) {
        const ix = arr.indexOf(elm);
        if (ix >= 0)
            arr.splice(ix, 1);
    },
    unique<T>(arr: T[]): T[] {
        const newarr: T[] = [];
        for (const el of arr) {
            if (newarr.indexOf(el) < 0)
                newarr.push(el);
        }
        return newarr;
    },
};

export const String: StringUtils = {
    capitalize<S extends string>(string: S): string {
        return string[0].toUpperCase() + string.slice(1) as Capitalize<S>;
    },
    endsWith: extractPrototypeMethod(_String, "endsWith"),
    includes: extractPrototypeMethod(_String, "includes"),
    // extractPrototypeMethod gets the type of the wrong overload
    replaceAllLiteral: extractPrototypeMethod(_String, "replaceAll") as unknown as StringUtils["replaceAllLiteral"],
    startsWith: extractPrototypeMethod(_String, "startsWith"),
};
