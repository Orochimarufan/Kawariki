import type { ArrayUtils, EntryMapFn, ObjectUtils, StringUtils } from "./es-polyfill.d.mts";

// ---------------------- Polyfills -----------------------------
// need to support back to NWjs 0.12.3/Chromium 41 for RMMV
function extractPrototypeMethod<F>(obj: Function, name: string): any {
    const fn = obj.prototype[name];
    return fn ? fn.call.bind(fn) : undefined;
}

const _Object = globalThis.Object;
const _Array = globalThis.Array;
const _String = globalThis.String;

export const Object: ObjectUtils = (() => {
    const keys = _Object.keys as <K extends string|number|symbol>(o: Record<K, any>) => K[];

    const assign: <T extends {}, U>(target: T, source: U) => T & U = (
        ((_Object as any).assign as <T extends {}, U>(target: T, source: U) => T & U) ??
        (<T extends {}, U extends {}>(target: T, source: U) => {
            keys(source).forEach(key => target[key] = source[key]);
            return target as T & U;
        }));

    const entries: <K extends string, T>(o: Partial<Record<K, T>>) => [K, T][] = (
        ((_Object as any).entries) ??
        (<K extends string, T>(obj: Record<K, T>) =>
            keys(obj).map(k => [k, obj[k]])));
    
    const fromEntries: <T = any>(entries: readonly [PropertyKey, T][]) => { [k: string]: T } = (
        ((_Object as any).fromEntries) ??
        (<T = any,>(entries: readonly [string|number, T][]) => {
            const res: {[k in string]: T} = {};
            for (const [k, v] of entries) res[k] = v;
            return res;
        }));

    const mapEntries: <K extends string|number|symbol, V, RK extends string|number|symbol, RV>(obj: Record<K, V>, fn: EntryMapFn<K,V,RK,RV>) => Record<RK, RV> = (
        (_Object as any).fromEntries !== undefined
        ? <K extends string|number|symbol,V,RK extends string|number|symbol,RV>(obj: Record<K,V>, fn: EntryMapFn<K,V,RK,RV>) =>
            fromEntries(entries(obj).map(fn as any) as [RK,RV][]) as Record<RK, RV>
        : <K extends string|number|symbol,V,RK extends string|number|symbol,RV>(obj: Record<K,V>, fn: EntryMapFn<K,V,RK,RV>) => {
            const newobj: Partial<Record<RK, RV>> = {};
            keys(obj).forEach(k => {
                const entry = fn([k as K, obj[k as K]]);
                newobj[entry[0]] = entry[1];
            });
            return newobj as Record<RK, RV>;
        });
    
    return {assign, entries, fromEntries, keys, mapEntries};
})();

export const Array: ArrayUtils = (() => {
    function flatMap<T, R>(arr: T[], fn: (el: T) => R[]): R[] {
        return _Array.prototype.concat.apply([], arr.map(fn));
    }

    const includes: <T>(arr: T[], elem: T) => boolean = (
        extractPrototypeMethod(_Array, 'includes') ??
        ((arr, elem) => arr.indexOf(elem) !== -1)
    );

    function removeInPlace<T>(arr: T[], elm: T) {
        const ix = arr.indexOf(elm);
        if (ix >= 0)
            arr.splice(ix, 1);
    };

    function unique<T>(arr: T[]): T[] {
        const newarr: T[] = [];
        for (const el of arr) {
            if (newarr.indexOf(el) < 0)
                newarr.push(el);
        }
        return newarr;
    }

    return {flatMap, includes, removeInPlace, unique};
})();

export const String: StringUtils = (() => {
    function capitalize<S extends string>(string: S): string {
        return string[0].toUpperCase() + string.slice(1) as Capitalize<S>;
    }

    const endsWith: (string: string, searchString: string, endPosition?: number) => boolean = (
        extractPrototypeMethod(_String, 'endsWith') ??
        ((str, end, endp) => {
            endp ??= str.length;
            return str.slice(endp - end.length, endp) == end;
        })
    );

    const includes: (string: string, searchString: string) => boolean = (
        extractPrototypeMethod(_String, 'includes') ??
        ((str, ss) => str.indexOf(ss) !== -1)
    );

    const replaceAllLiteral: (string: string, searchString: string, replacement: string) => string = (
        extractPrototypeMethod(_String, 'replaceAll') ??
        ((str, ss, repl) => {
            if (ss.length == 0)
                throw new Error();
            let ix = str.indexOf(ss);
            let from = 0;
            let parts: string[] = [];
            while (ix > -1) {
                const end = ix + ss.length;
                parts.push(str.substring(from, end));
                from = end;
            }
            if (from == 0)
                return str;
            parts.push(str.substring(from));
            return parts.join(repl);
        })
    )

    const startsWith: (string: string, searchString: string, position?: number) => boolean = (
        extractPrototypeMethod(_String, 'startsWith') ??
        ((str, ss, startp) => {
            startp ??= 0;
            return str.slice(startp, startp + ss.length) == ss;
        })
    );

    return {capitalize, endsWith, includes, replaceAllLiteral, startsWith};
})();
