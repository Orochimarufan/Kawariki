// RPGMaker MV/MZ Variable inspection utilities

export type VarType = "variable"|"switch";

/**
 * Represents a reference to a RPGMaker variable
 */
export class Var<T=any> {
    static NAMESPACES: Record<VarType, {names: () => string[], values: () => any[]}> = {
        "variable": {
            "names": () => $dataSystem.variables,
            "values": () => $gameVariables._data,
        },
        "switch": {
            "names": () => $dataSystem.switches,
            "values": () => $gameSwitches._data,
        }
    };

    readonly ns: VarType;
    readonly id: number;
    readonly name: string;
    private readonly _data: () => any[];
    private lastValue: T;

    /**
     * Easy access to RPGMaker variables
     * @param ns The id namespace
     * @param id The variable id
     */
    constructor(ns: VarType, id: number) {
        this.ns = ns;
        this.id = id;
        const space = Var.NAMESPACES[ns];
        this.name = space.names()[id];
        this._data = space.values;
        this.lastValue = this._read();
    }

    private _read(): T {
        return this._data()[this.id];
    }

    private _write(value: T) {
        this._data()[this.id] = value;
    }

    /**
     * Retrieve the variable content
     */
    get(): T {
        return this.lastValue = this._read();
    }

    /**
     * Set the variable
     */
    set(value: T) {
        this._write(this.lastValue = value);
    }

    /**
     * Check if the variable has changed since the last call
     * to either hasChanged() or set()
     * @note This doesn't modify the changed status
     * @sa hasChanged()
     * @returns Wether the variable changed recently
     */
    pollChanged() {
        return this.lastValue !== this._read();
    }

    /**
     * Check if the variable has changed since the last call
     * to either hasChanged() or set()
     * @note This resets the changed status
     * @sa pollChanged()
     * @returns Wether the variable changed recently
     */
    hasChanged() {
        const new_value = this._read();
        const changed = this.lastValue !== new_value;
        this.lastValue = new_value;
        return changed;
    }

    static *_fmchain<T=any, U=any>(fn: (x: T, i: number, iter: T[]) => U|undefined, ...args: T[][]): Generator<U> {
        for (let iter of args) {
            let i = 0;
            for (let x of iter) {
                let res = fn(x, i, iter);
                if (res !== undefined)
                    yield res;
            }
        }
    }

    /**
     * Find variables that currently have a specific value
     * @param value The value to look for
     */
    static findValue<T=any>(value: T): VarList<T> {
        return VarList.from(this._fmchain(
            (v, i) => (v === value ? new this("variable", i) : undefined),
            $gameVariables._data));
    }

    /**
     * Find a variable or switch by name
     */
    static findName(name: string): VarList<any> {
        return VarList.from(this._fmchain(
            (n, i, it) => (n.includes(name) ? new this(it === $dataSystem.variables ? "variable" : "switch", i) : undefined),
            $dataSystem.variables, $dataSystem.switches));
    }

    /**
     * Get all variables
     */
    static allVariables(): VarList<any> {
        return VarList.from($gameVariables._data
            .map((_, i) => new this("variable", i)));
    }

    /**
     * Get all switches
     */
    static allSwitches(): VarList<boolean> {
        return VarList.from($gameSwitches._data
            .map((_, i) => new this("switch", i)));
    }

    toString() {
        return `[${this.name}] = ${this.get()}`;
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
    static from_ids<NS extends VarType>(ns: NS, ids: number[]): VarList<NS extends "switch"?boolean:any> {
        return this.from(ids.map(i => new Var(ns, i))) as VarList;
    }
}


// Add globals on window
declare global {
    var RpgVariable: typeof Var;
    var RpgVariableList: typeof VarList;
}

window.RpgVariable = Var;
window.RpgVariableList = VarList;
