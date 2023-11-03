// RPG Variable inspection utilities

/**
 * @typedef {"variable"|"switch"} RpgVariable_NS
 */

/**
 * Represents a reference to a RPGMaker variable
 * @template [T=any]
 */
class RpgVariable {
    /** @type {Record<RpgVariable_NS, {names: () => string[], values: () => any[]}} */
    static NAMESPACES = {
        "variable": {
            "names": () => $dataSystem.variables,
            "values": () => $gameVariables._data,
        },
        "switch": {
            "names": () => $dataSystem.switches,
            "values": () => $gameSwitches._data,
        }
    }

    /**
     * Easy access to RPGMaker variables
     * @param {RpgVariable_NS} ns The id namespace
     * @param {number} id The variable id
     */
    constructor(ns, id) {
        this.ns = ns;
        this.id = id;
        const space = RpgVariable.NAMESPACES[ns];
        this.name = space.names()[id];
        this._data = space.values;
        this.lastValue = this._read();
    }

    _read() {
        return this._data()[this.id];
    }

    _write(value) {
        this._data()[this.id] = value;
    }

    /**
     * Retrieve the variable content
     * @returns {T}
     */
    get() {
        return this.lastValue = this._read();
    }

    /**
     * Set the variable
     * @param {T} value
     */
    set(value) {
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

    /**
     * Find variables that currently have a specific value
     * @param {any} value The value to look for
     * @returns {RpgVariableList<any>}
     */
    static findValue(value) {
        return RpgVariableList.from($gameVariables._data
            .map((n, i) => [i, n])
            .filter(([_, v]) => v === value)
            .map(([i, _]) => new this("variable", i)));
    }

    /**
     * Find a variable or switch by name
     * @param {string} name
     * @returns {RpgVariableList<any>}
     */
    static findName(name) {
        return RpgVariableList.from(
            ($dataSystem.variables
                .map((n, i) => ["variable", i, n])
                + $dataSystem.switches
                .map((n, i) => ["switch", i, n]))
            .filter(([_, _1, n]) => n.includes(name))
            .map(([z, i, _]) => new this(z, i)));
    }

    /**
     * Get all variables
     * @returns {RpgVariableList<any>}
     */
    static allVariables() {
        return RpgVariableList.from($gameVariables._data
            .map((_, i) => new this("variable", i)));
    }

    /**
     * Get all switches
     * @returns {RpgVariableList<boolean>}
     */
    static allSwitches() {
        return RpgVariableList.from($gameSwitches._data
            .map((_, i) => new this("switch", i)));
    }

    toString() {
        return `[${this.name}] = ${this.get()}`;
    }
}

/**
 * A list of RPGMaker variables
 * @template [T=any]
 * @extends {Array<RpgVariable<T>>}
 */
class RpgVariableList extends Array {
    /**
     * Filter array in place
     * @param {(v: RpgVariable, i: number, a: RpgVariableList) => boolean} condition
     * @returns {this}
     */
    narrow(condition) {
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
     * @param {any} value
     * @returns {this}
     */
    narrowValue(value) {
        return this.narrow(v => v.get() === value);
    }

    /**
     * Narrow list by checking which variables have recently changed
     * @returns {this}
     */
    narrowChanges() {
        return this.narrow(v => v.hasChanged());
    }

    /**
     * Create new array from variable ids
     * @param {RpgVariable_NS} ns ID namespace
     * @param {number[]} ids The variable ids
     * @returns {this}
     */
    static from_ids(ns, ids) {
        return this.from(ids.map(i => new RpgVariable(ns, i)));
    }
}
