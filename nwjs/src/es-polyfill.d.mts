// Slightly extended ES library polyfill
// Note: Object methods map key types, unlike standard TypeScript definitions
// Note: We don't modify the global objects directly, instead exporting
//       our own objects with static methods. The game may later replace
//       methods on the globals with it's own polyfills.

export type EntryMapFn<K extends string|number|symbol, V, RK extends string|number|symbol, RV> = (entry: [K, V]) => [RK, RV];

export interface ObjectUtils {
    keys<K extends string|number|symbol>(o: Record<K, any>): K[];
    assign<T extends {}, U>(target: T, source: U): T & U;
    entries<K extends string, T>(o: Partial<Record<K, T>>): [K, T][];
    fromEntries<T = any>(entries: readonly [PropertyKey, T][]): { [k: string]: T };
    // Like fromEntries(entries(obj).map(fn))
    mapEntries<K extends string|number|symbol, V, RK extends string|number|symbol, RV>(obj: Record<K, V>, fn: EntryMapFn<K,V,RK,RV>): Record<RK, RV>;
}

export interface ArrayUtils {
    flatMap<T, R>(arr: T[], fn: (el: T) => R[]): R[];
    includes<T>(arr: T[], elem: T): boolean;
    // Remove an element in-place
    removeInPlace<T>(arr: T[], elm: T): void;
    // Create new Array with duplicates removed
    unique<T>(arr: T[]): T[];
}

export interface StringUtils {
    capitalize(string: string): string;
    endsWith(string: string, searchString: string, endPosition?: number): boolean;
    includes(string: string, searchString: string): boolean;
    // Like replaceAll, but only accepts string arguments
    replaceAllLiteral(string: string, searchString: string, replacement: string): string;
    startsWith(string: string, searchString: string, position?: number): boolean;
}
