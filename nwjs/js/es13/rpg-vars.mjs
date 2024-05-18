function* filterMapChain(iter, mapper, ...args) {
    for (const obj of args) {
        const it = iter(obj);
        for (const x of it) {
            const res = mapper(x, obj);
            if (res !== undefined)
                yield res;
        }
    }
}
function* iterNamespaceImpl(names, values) {
    for (const [i, name] of names.entries()) {
        const value = values[i];
        if (name !== '' || (value !== undefined && value !== null))
            yield [i, name, value];
    }
    const offset = names.length;
    for (const [j, value] of values.slice(offset).entries()) {
        if (value !== undefined && value !== null)
            yield [offset + j, '', value];
    }
    ;
}
export const VARIABLE = {
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
export const SWITCH = {
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
};
function resolveNs(ns) {
    if (typeof ns === 'string') {
        const r = NAMESPACES[ns];
        if (r === undefined)
            throw new Error(`Unknown namespace key: '${ns}'. Available namespaces are: ${Object.keys(NAMESPACES).join(', ')}`);
        return r;
    }
    return ns;
}
const nothing = Symbol();
export class Var {
    ns;
    id;
    name;
    value;
    constructor(ns, id, name, value = nothing) {
        this.ns = ns;
        this.id = id;
        this.name = name ?? ns.getName(id);
        this.value = value === nothing ? ns.read(id) : value;
    }
    get lastValue() {
        return this.value;
    }
    get() {
        return this.value = this.ns.read(this.id);
    }
    peek() {
        return this.ns.read(this.id);
    }
    set(value) {
        this.ns.write(this.id, this.value = value);
    }
    pollChanged() {
        return this.value !== this.ns.read(this.id);
    }
    hasChanged() {
        const new_value = this.ns.read(this.id);
        const changed = this.value !== new_value;
        this.value = new_value;
        return changed;
    }
    toString() {
        return `${this.ns.name}[${this.name}] = ${this.value}`;
    }
    static at(ns, id) {
        return new this(NAMESPACES[ns], id);
    }
    static enumerate(...nss) {
        return VarList.from(filterMapChain(ns => ns.iter(), ([id, name, value], ns) => new this(ns, id, name, value), ...(nss.length ? nss.map(resolveNs) : Object.values(NAMESPACES))));
    }
    static findValue(value, ...nss) {
        return VarList.from(filterMapChain(ns => ns.iterValues(), ([i, v], ns) => (v === value ? new this(ns, i, undefined, v) : undefined), ...(nss.length ? nss.map(resolveNs) : Object.values(NAMESPACES))));
    }
    static findName(name, ...nss) {
        return VarList.from(filterMapChain(ns => ns.iterNames(), ([i, n], ns) => (n.includes(name) ? new this(ns, i, n) : undefined), ...(nss.length ? nss.map(resolveNs) : Object.values(NAMESPACES))));
    }
    static allVariables() {
        return this.enumerate(VARIABLE);
    }
    static allSwitches() {
        return this.enumerate(SWITCH);
    }
}
export class VarList extends Array {
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
        const n = resolveNs(ns);
        return this.from(ids.map(i => new Var(n, i)));
    }
}
window.RpgVariable = Var;
//# sourceMappingURL=rpg-vars.mjs.map