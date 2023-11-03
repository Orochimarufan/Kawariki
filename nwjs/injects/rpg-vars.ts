// RPG Variable inspection utilities


type RpgVariable_NS = "variable"|"switch";

/**
 * Represents a reference to a RPGMaker variable
 */
class RpgVariable<T=any> {
    static NAMESPACES: Record<RpgVariable_NS, {names: () => string[], values: () => any[]}> = {
        "variable": {
            "names": () => $dataSystem.variables,
            "values": () => $gameVariables._data,
        },
        "switch": {
            "names": () => $dataSystem.switches,
            "values": () => $gameSwitches._data,
        }
    };

    readonly ns: RpgVariable_NS;
    readonly id: number;
    readonly name: string;
    private readonly _data: () => any[];
    private lastValue: T;

    /**
     * Easy access to RPGMaker variables
     * @param ns The id namespace
     * @param id The variable id
     */
    constructor(ns: RpgVariable_NS, id: number) {
        this.ns = ns;
        this.id = id;
        const space = RpgVariable.NAMESPACES[ns];
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
    static findValue<T=any>(value: T): RpgVariableList<T> {
        return RpgVariableList.from(this._fmchain(
            (v, i) => (v === value ? new this("variable", i) : undefined),
            $gameVariables._data));
    }

    /**
     * Find a variable or switch by name
     */
    static findName(name: string): RpgVariableList<any> {
        return RpgVariableList.from(this._fmchain(
            (n, i, it) => (n.includes(name) ? new this(it === $dataSystem.variables ? "variable" : "switch", i) : undefined),
            $dataSystem.variables, $dataSystem.switches));
    }

    /**
     * Get all variables
     */
    static allVariables(): RpgVariableList<any> {
        return RpgVariableList.from($gameVariables._data
            .map((_, i) => new this("variable", i)));
    }

    /**
     * Get all switches
     */
    static allSwitches(): RpgVariableList<boolean> {
        return RpgVariableList.from($gameSwitches._data
            .map((_, i) => new this("switch", i)));
    }

    toString() {
        return `[${this.name}] = ${this.get()}`;
    }
}

/**
 * A list of RPGMaker variables
 */
class RpgVariableList<T=any> extends Array<RpgVariable<T>> {
    /**
     * Filter array in place
     */
    narrow(condition: (v: RpgVariable, i: number, a: RpgVariableList) => boolean): this {
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
    static from<T=any>(iter: Iterable<RpgVariable<T>>|ArrayLike<RpgVariable<T>>): RpgVariableList<T> {
        return super.from(iter) as RpgVariableList<T>;
    }

    /**
     * Create new array from variable ids
     */
    static from_ids<NS extends RpgVariable_NS>(ns: NS, ids: number[]): RpgVariableList<NS extends "switch"?boolean:any> {
        return this.from(ids.map(i => new RpgVariable(ns, i))) as RpgVariableList;
    }
}
