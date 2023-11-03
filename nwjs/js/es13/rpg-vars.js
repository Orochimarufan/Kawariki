class RpgVariable {
    static NAMESPACES = {
        "variable": {
            "names": () => $dataSystem.variables,
            "values": () => $gameVariables._data,
        },
        "switch": {
            "names": () => $dataSystem.switches,
            "values": () => $gameSwitches._data,
        }
    };
    ns;
    id;
    name;
    _data;
    lastValue;
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
    get() {
        return this.lastValue = this._read();
    }
    set(value) {
        this._write(this.lastValue = value);
    }
    pollChanged() {
        return this.lastValue !== this._read();
    }
    hasChanged() {
        const new_value = this._read();
        const changed = this.lastValue !== new_value;
        this.lastValue = new_value;
        return changed;
    }
    static *_fmchain(fn, ...args) {
        for (let iter of args) {
            let i = 0;
            for (let x of iter) {
                let res = fn(x, i, iter);
                if (res !== undefined)
                    yield res;
            }
        }
    }
    static findValue(value) {
        return RpgVariableList.from(this._fmchain((v, i) => (v === value ? new this("variable", i) : undefined), $gameVariables._data));
    }
    static findName(name) {
        return RpgVariableList.from(this._fmchain((n, i, it) => (n.includes(name) ? new this(it === $dataSystem.variables ? "variable" : "switch", i) : undefined), $dataSystem.variables, $dataSystem.switches));
    }
    static allVariables() {
        return RpgVariableList.from($gameVariables._data
            .map((_, i) => new this("variable", i)));
    }
    static allSwitches() {
        return RpgVariableList.from($gameSwitches._data
            .map((_, i) => new this("switch", i)));
    }
    toString() {
        return `[${this.name}] = ${this.get()}`;
    }
}
class RpgVariableList extends Array {
    narrow(condition) {
        let j = 0;
        this.forEach((e, i) => {
            if (condition(e, i, this)) {
                if (i !== j)
                    this[j] = e;
                j++;
            }
        });
        this.length = j;
        return this;
    }
    narrowValue(value) {
        return this.narrow(v => v.get() === value);
    }
    narrowChanges() {
        return this.narrow(v => v.hasChanged());
    }
    static from(iter) {
        return super.from(iter);
    }
    static from_ids(ns, ids) {
        return this.from(ids.map(i => new RpgVariable(ns, i)));
    }
}
//# sourceMappingURL=rpg-vars.js.map