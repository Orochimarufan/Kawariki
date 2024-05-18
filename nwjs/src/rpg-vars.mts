// RPGMaker MV/MZ Variable inspection utilities

// --------------------------------------------------------
// Iterable utilities
function *filterMapChain<T=any, V=any, U=any>(iter: (obj: T) => Iterable<V>, mapper: (x: V, c: T) => U|undefined, ...args: T[]): Generator<U> {
    for (const obj of args) {
        const it = iter(obj);
        for (const x of it) {
            const res = mapper(x, obj);
            if (res !== undefined)
                yield res;
        }
    }
}


// --------------------------------------------------------
// RPGMaker variable namespaces
export interface Namespace<T=any> {
    name: string,
    getName(id: number): string,
    read(id: number): T,
    write(id: number, value: T): void,
    // Iterate over all known entries (either named or set)
    iter(): Iterable<[number, string, T]>,
    // Iterate over all known names (omits unnamed entries)
    iterNames(): Iterable<[number, string]>,
    // Iterator over all set values (omits undefined entries)
    iterValues(): Iterable<[number, T]>,
}

function *iterNamespaceImpl<T>(names: string[], values: T[]): Generator<[number, string, T]> {
    // values may be sparse
    for (const [i, name] of names.entries()) {
        const value = values[i];
        if (name !== '' || (value !== undefined && value !== null))
            yield [i, name, value];
    }
    const offset = names.length;
    for (const [j, value] of values.slice(offset).entries()) {
        if (value !== undefined && value !== null)
            yield [offset + j, '', value];
    };
}

export const VARIABLE: Namespace = {
    name: "variable",
    getName(index) {
        return $dataSystem.variables[index];
    },
    read(index) {
        return $gameVariables._data[index];
    },
    write(index, value) {
        $gameVariables._data[index] = value;
    },
    iter() {
        return iterNamespaceImpl($dataSystem.variables, $gameVariables._data);
    },
    iterNames() {
        return $dataSystem.variables.entries();
    },
    iterValues() {
        return $gameVariables._data.entries();
    },
};

export const SWITCH: Namespace<boolean> = {
    name: "switch",
    getName(index) {
        return $dataSystem.switches[index];
    },
    read(index) {
        return $gameSwitches._data[index];
    },
    write(index, value) {
        $gameSwitches._data[index] = value;
    },
    iter() {
        return iterNamespaceImpl($dataSystem.switches, $gameSwitches._data);
    },
    iterNames() {
        return $dataSystem.switches.entries();
    },
    iterValues() {
        return $gameSwitches._data.entries();
    },
};

export const NAMESPACES = {
    "variable": VARIABLE,
    "switch": SWITCH,
} satisfies Record<string, Namespace>;

export type NsKey = keyof typeof NAMESPACES;

function resolveNs(ns: Namespace|NsKey): Namespace {
    if (typeof ns === 'string') {
        const r = NAMESPACES[ns];
        if (r === undefined)
            throw new Error(`Unknown namespace key: '${ns}'. Available namespaces are: ${Object.keys(NAMESPACES).join(', ')}`);
        return r;
    }
    return ns;
}


// --------------------------------------------------------
const nothing = Symbol();
type Nothing = typeof nothing;

/**
 * Represents a reference to a RPGMaker variable
 */
export class Var<T=any> {
    readonly ns: Namespace;
    readonly id: number;
    readonly name: string;
    private value: T;

    /**
     * Easy access to RPGMaker variables
     * @param ns The variable namespace
     * @param id The variable id inside the namespace
     */
    constructor(ns: Namespace, id: number);
    constructor(ns: Namespace, id: number, name?: string, value?: T);
    constructor(ns: Namespace, id: number, name?: string, value: T|Nothing=nothing) {
        this.ns = ns;
        this.id = id;
        this.name = name ?? ns.getName(id);
        this.value = value === nothing ? ns.read(id) : value;
    }

    /**
     * The value the variable had when we last interacted with it
     * This is mainly used for change tracking
     */
    get lastValue(): T {
        return this.value;
    }

    /**
     * Retrieve the variable content
     * @returns The value currently assigned to the variable
     * @note Updates lastValue
     * @see poll()
     */
    get(): T {
        return this.value = this.ns.read(this.id);
    }

    /**
     * Retrieve the variable content without updating lastValue
     * @returns The value currently assigned to the variable
     * @note Doesn't update lastValue
     * @see get()
     */
    peek(): T {
        return this.ns.read(this.id);
    }

    /**
     * Set the variable
     * @param value The new value to set the variable to
     * @note Updates lastValue
     */
    set(value: T): void {
        this.ns.write(this.id, this.value = value);
    }

    /**
     * Check if the variable has changed since the last update of lastValue
     * @returns Wether the variable changed recently
     * @note Doesn't update lastValue
     * @see hasChanged()
     */
    pollChanged() {
        return this.value !== this.ns.read(this.id);
    }

    /**
     * Check if the variable has changed since the last update of lastValue
     * @returns Wether the variable changed recently
     * @note Updates lastValue
     * @see pollChanged()
     */
    hasChanged() {
        const new_value = this.ns.read(this.id);
        const changed = this.value !== new_value;
        this.value = new_value;
        return changed;
    }

    toString() {
        return `${this.ns.name}[${this.name}] = ${this.value}`;
    }

    // =========== Constructors =================
    /**
     * Create a Variable reference from it's type and ID
     * @param ns The RPGMaker variable type: 'variable' or 'switch'
     * @param id The ID/Index of the variable
     * @returns A new Var instance
     */
    static at<T=any>(ns: NsKey, id: number): Var<T> {
        return new this(NAMESPACES[ns], id);
    }

    // =========== List Constructors ============
    /**
     * Enumerate all (known) variables in a namespace
     * @param ns The namespace to enumerate
     * @returns A new VarList
     */
    static enumerate(): VarList;
    static enumerate<T=any>(...nss: Namespace<T>[]): VarList<T>;
    static enumerate<Key extends NsKey>(ns: Key): VarList<typeof NAMESPACES[Key] extends Namespace<infer T> ? T : any>;
    static enumerate<Key extends NsKey>(...nss: Key[]): VarList;
    static enumerate(...nss: (Namespace|NsKey)[]): VarList {
        return VarList.from(filterMapChain(
            ns => ns.iter(),
            ([id, name, value], ns) => new this(ns, id, name, value),
            ...(nss.length ? nss.map(resolveNs) : Object.values(NAMESPACES)),
        ));
    }

    /**
     * Find variables that currently have a specific value (exact match)
     * @param value The value to look for
     */
    static findValue<T>(value: T): VarList<T>;
    static findValue<T>(value: T, ...nss: Namespace<T>[]): VarList<T>;
    static findValue<T>(value: T, ...nss: NsKey[]): VarList<T>;
    static findValue<T>(value: T, ...nss: (Namespace|NsKey)[]): VarList<T> {
        return VarList.from(filterMapChain(
            ns => ns.iterValues(),
            ([i, v], ns) => (v === value ? new this(ns, i, undefined, v) : undefined),
            ...(nss.length ? nss.map(resolveNs) : Object.values(NAMESPACES)),
        ));
    }

    /**
     * Find a variable or switch by name (substring)
     */
    static findName(name: string): VarList;
    static findName<T=any>(name: string, ...nss: Namespace<T>[]): VarList<T>;
    static findName<Key extends NsKey>(name: string, ns: Key): VarList<typeof NAMESPACES[Key] extends Namespace<infer T> ? T : any>;
    static findName<Key extends NsKey>(name: string, ...nss: Key[]): VarList;
    static findName(name: string, ...nss: (Namespace|NsKey)[]): VarList {
        return VarList.from(filterMapChain(
            ns => ns.iterNames(),
            ([i, n], ns) => (n.includes(name) ? new this(ns, i, n) : undefined),
            ...(nss.length ? nss.map(resolveNs) : Object.values(NAMESPACES)),
        ));
    }

    // Shortcuts
    /**
     * Get all variables
     * @note Short for enumerate(VARIABLE)
     */
    static allVariables(): VarList {
        return this.enumerate(VARIABLE);
    }

    /**
     * Get all switches
     * @note Short for enumerate(SWITCH)
     */
    static allSwitches(): VarList<boolean> {
        return this.enumerate(SWITCH);
    }
}

/**
 * A list of RPGMaker variables
 */
export class VarList<T=any> extends Array<Var<T>> {
    /**
     * Filter array in place
     */
    narrow(condition: (v: Var, i: number, a: VarList) => boolean): this {
        let j = 0;
        this.forEach((e, i) => {
            if (condition(e, i, this)) {
                if (i!==j)
                    this[j] = e;
                j++;
            }
        });
        this.length = j;
        return this;
    }

    /**
     * Narrow list by current value
     */
    narrowValue(value: any): this {
        return this.narrow(v => v.get() === value);
    }

    /**
     * Narrow list by checking which variables have recently changed
     */
    narrowChanges(): this {
        return this.narrow(v => v.hasChanged());
    }

    // Correct typing for Array.from
    static from<T=any>(iter: Iterable<Var<T>>|ArrayLike<Var<T>>): VarList<T> {
        return super.from(iter) as VarList<T>;
    }

    /**
     * Create new array from variable ids
     */
    static from_ids<Ns extends Namespace>(ns: Ns, ids: number[]): VarList<Ns extends Namespace<infer T> ? T : any>;
    static from_ids<Key extends NsKey>(ns: Key, ids: number[]): VarList<typeof NAMESPACES[Key] extends Namespace<infer T> ? T : any>;
    static from_ids(ns: Namespace|NsKey, ids: number[]): VarList<any> {
        const n = resolveNs(ns);
        return this.from(ids.map(i => new Var(n, i))) as VarList;
    }
}


// Add globals on window
declare global {
    var RpgVariable: typeof Var;
    //var RpgVariableList: typeof VarList;
}

window.RpgVariable = Var;
//window.RpgVariableList = VarList;
