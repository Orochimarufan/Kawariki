// Key mapping. Assumes US-Keyboard
// TODO: make configurable somehow
// Ideally GUI?

// ---------------------------- External ----------------------
// RPGMaker core
type _Action = 'tab'|'shift'|'control'|'escape'|'debug'|'pageup'|'pagedown'|'up'|'left'|'down'|'right'|'ok';
declare const Imported: Record<string, any>|undefined;
declare const Input: {
    keyMapper: Record<number, _Action|string>,
    _switchButton?: (button: string) => void, // Yanfly
    _revertButton?: (button: string) => void, // Yanfly
};
// Yanfly plugin
declare const Yanfly: any;
// QInput plugin
type _QAction = _Action|'fps'|'streched'|'fullscreen'|'restart'|'console';
declare const QInput: undefined|{
    remapped: {[k in _QAction]: string},
    keys: {[k: number]: string},
};
declare const ConfigManager: {
    keys?: {[a in _QAction]: string|string[]}
};

(() => {
    // Typing helpers
    const id: <T>(t: T) => T = (o) => o;
    var _key: <T>(et: { [K in keyof T]: number }) => typeof et = id;
    var _action: <T>(et: { [K in keyof T]: _Action }) => typeof et = id;

    // ------------------------ Constants ---------------------
    /** All valid key constants */
    const key = _key({
        backspace: 8,
        tab: 9,
        clear: 12,
        enter: 13,
        shift: 16,
        control: 17,
        alt: 18,
        pause: 19,
        caps: 20,
        esc: 27,
        space: 32,
        pageup: 33,
        pagedown: 34,
        end: 35,
        home: 36,
        left: 37,
        up: 38,
        right: 39,
        down: 40,
        select: 41,
        print: 42,
        execute: 43,
        printscreen: 44,
        insert: 45,
        delete: 46,
        help: 47,
        k0: 48,
        k1: 49,
        k2: 50,
        k3: 51,
        k4: 52,
        k5: 53,
        k6: 54,
        k7: 55,
        k8: 56,
        k9: 57,
        a: 65,
        b: 66,
        c: 67,
        d: 68,
        e: 69,
        f: 70,
        g: 71,
        h: 72,
        i: 73,
        j: 74,
        k: 75,
        l: 76,
        m: 77,
        n: 78,
        o: 79,
        p: 80,
        q: 81,
        r: 82,
        s: 83,
        t: 84,
        u: 85,
        v: 86,
        w: 87,
        x: 88,
        y: 89,
        z: 90,
        meta_left: 91,
        meta_right: 92,
        context: 93,
        n0: 96,
        n1: 97,
        n2: 98,
        n3: 99,
        n4: 100,
        n5: 101,
        n6: 102,
        n7: 103,
        n8: 104,
        n9: 105,
        n_mult: 106,
        n_add: 107,
        n_enter: 108,
        n_subtract: 109,
        n_point: 110,
        n_divide: 111,
        f1: 112,
        f2: 113,
        f3: 114,
        f4: 115,
        f5: 116,
        f6: 117,
        f7: 118,
        f8: 119,
        f9: 120,
        f10: 121,
        f11: 122,
        f12: 123,
        f13: 124,
        f14: 125,
        f15: 126,
        f16: 127,
        f17: 128,
        f18: 129,
        f19: 130,
        f20: 131,
        f21: 132,
        f22: 133,
        f23: 134,
        f24: 135,
        f25: 136,
        f26: 137,
        f27: 138,
        f28: 139,
        f29: 140,
        f30: 141,
        f31: 142,
        f32: 143,
        numlock: 144,
        scrolllock: 145,
        page_back: 166,
        page_forward: 167,
        page_reload: 168,
        vol_down: 174,
        vol_up: 175,
        semicolon: 186,
        equals: 187,
        comma: 188,
        dash: 189,
        period: 190,
        slash: 191,
        grave: 192,
        bracket_open: 219,
        backslash: 220,
        bracket_close: 221,
        quote: 222,
    });

    /** Pre-defined standatd action names */
    const action = _action({
        tab: 'tab',
        shift: 'shift',
        control: 'control',
        escape: 'escape',
        debug: 'debug',
        pageup: 'pageup',
        pagedown: 'pagedown',
        up: 'up',
        left: 'left',
        down: 'down',
        right: 'right',
        ok: 'ok',
        confirm: 'ok',
        cancel: 'escape',
    });

    type Key = keyof typeof key;
    type Action = keyof typeof action;
    type Map = {[P in Key]?: Action|string};

    // ------------------------ Settings ----------------------
    /** Initial Keymap Customizations */
    const map: Map  = {
        w: 'up',
        a: 'left',
        s: 'down',
        d: 'right',
        e: 'confirm',
        q: 'cancel',
        r: 'pageup',
        f: 'pagedown',
    };

    /** Special options */
    const options = {
        overrideBCE: false,
    };

    // ------------------------ Polyfills ---------------------
    // need to support back to NWjs 0.12.3/Chromium 41 for RMMV
    const _object = Object as {
        entries?: <T>(o: { [s: string]: T } | ArrayLike<T>) => [string, T][],
        fromEntries?: <T = any>(entries: readonly [PropertyKey, T][]) => { [k: string]: T },
        assign?: <T extends {}, U>(target: T, source: U) => T & U,
    };
    type EntryMapFn<K extends string|number|symbol, V, RK extends string|number|symbol, RV> = (entry: [K, V]) => [RK, RV];

    /** Map over Object entries (polyfill) */
    const Object_mapEntries: <K extends string|number|symbol, V, RK extends string|number|symbol, RV>(obj: Record<K, V>, fn: EntryMapFn<K,V,RK,RV>) => Record<RK, RV> = (
        _object.fromEntries !== undefined
        ? <K extends string|number|symbol,V,RK extends string|number|symbol,RV>(obj: Record<K,V>, fn: EntryMapFn<K,V,RK,RV>) =>
            _object.fromEntries(_object.entries(obj).map(fn as any) as [RK,RV][]) as Record<RK, RV>
        : <K extends string|number|symbol,V,RK extends string|number|symbol,RV>(obj: Record<K,V>, fn: EntryMapFn<K,V,RK,RV>) => {
            const newobj: Partial<Record<RK, RV>> = {};
            Object.keys(obj).forEach(k => {
                const entry = fn([k as K, obj[k as K]]);
                newobj[entry[0]] = entry[1];
            });
            return newobj as Record<RK, RV>;
        });

    /** Object.entries polyfill */
    const Object_entries: <T>(o: { [s: string]: T } | ArrayLike<T>) => [string, T][] = _object.entries
        ?? (obj => Object.keys(obj).map(k => [k, obj[k]]));

    /** Object.fromEntries polyfill */
    const Object_fromEntries: <T = any>(entries: readonly [PropertyKey, T][]) => { [k: string]: T } = _object.fromEntries
        ?? (<T = any>(entries: readonly [string|number, T][]) => {
            const res: {[k in string]: T} = {};
            for (const [k, v] of entries) res[k] = v;
            return res;
        });

    /** Object.assign polyfill */
    const Object_assign: <T extends {}, U extends {}>(target: T, source: U) => T & U = _object.assign
        ?? (<T extends {}, U extends {}>(target: T, source: U) => {
            Object.keys(source).forEach(key => target[key] = source[key]);
            return target as T & U;
        });

    // ------------------------ Code --------------------------
    const keyByCode: Record<number, Key> = Object_mapEntries(key, ([key, code]) => [code, key]);

    type ApplyHook = (kas: [Key, Action|string][]) => void;
    const hook_vanilla: ApplyHook = kas => kas.forEach(([keyname, act]) => {
        Input.keyMapper[key[keyname]] = action[act] ?? act;
    });
    const hooks: ApplyHook[] = [hook_vanilla];

    function _apply(map: Map): void {
        const kas = Object_entries(map) as [Key, string][];
        hooks.forEach(hook => hook(kas));
    }

    /** Set a single key mapping */
    function set(keyname: Key, act: Action|string): void {
        map[keyname] = act;
        _apply({[keyname]: act});
    }

    /** Get currently active mappings from game core */
    function get(): Map {
        return Object_mapEntries(Input.keyMapper, ([code, coreAction]) => {
            const k = keyByCode[code];
            return [k !== undefined ? k : code, coreAction];
        });
    }

    /** Add new mappings */
    function add(mappings: Map): void {
        Object_assign(map, mappings);
        _apply(mappings);
    }

    /** Re-Apply custom mappings */
    function apply(): void {
        _apply(map);
    }

    // ------------------------ Plugins -----------------------
    // Yanfly ButtonCommonEvents support
    function setupYEP_BCE() {
        const YEP_BCE_switch_map: Record<string, _Action> = {
            OK: 'ok',
            CANCEL: 'escape',
            DASH: 'shift',
            PAGEUP: 'pageup',
            PAGEDOWN: 'pagedown',
            LEFT: 'left',
            UP: 'up',
            RIGHT: 'right',
            DOWN: 'down'
        };

        const YEP_BCE_key_map: {[K in Key]?: string} = {
            enter: 'enter',
            shift: 'keyShift',
            space: 'space',
            pageup: 'pageUp',
            pagedown: 'pageDown',
            end: 'end',
            home: 'home',
            left: 'dirLeft',
            up: 'dirUp',
            right: 'dirRight',
            down: 'dirDown',
            insert: 'ins',
            delete: 'del',
            n_mult: 'numTimes',
            n_add: 'numPlus',
            n_subtract: 'numMinus',
            n_point: 'numPeriod',
            n_divide: 'numDivide',
            equals: 'equal',
            dash: 'minus',
            period: 'period',
            slash: 'foreSlash',
            grave: 'tilde',
            bracket_open: 'foreBrack',
            backslash: 'backSlash',
            bracket_close: 'backBrack',
            quote: 'quote',
        };
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'].forEach(n => {
            YEP_BCE_key_map["k" + n] = n;
            YEP_BCE_key_map["n" + n] = "num" + n;
        });
        ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'].forEach(s => {
            YEP_BCE_key_map[s] = s;
        });

        const _switchButton = Input._switchButton as (button: string) => void;
        Input._switchButton = (button) => {
            _switchButton.call(Input, button);
            if (options.overrideBCE) {
                apply();
            } else if (button === 'ALL') {
                Object.keys(YEP_BCE_key_map).forEach(k => {
                    const y = YEP_BCE_key_map[k];
                    if (Yanfly.Param.BCEList[y] !== 0)
                        Input.keyMapper[key[k]] = y;
                });
            } else {
                const act = YEP_BCE_switch_map[button];
                Object.keys(map).forEach(k => {
                    if (map[k] === act) {
                        const y = YEP_BCE_key_map[k];
                        if (Yanfly.Param.BCEList[y] !== 0)
                            Input.keyMapper[key[k]] = y;
                    }
                });
            }
        };

        const _revertButton = Input._revertButton as (button: string) => void;
        Input._revertButton = function(button) {
            _revertButton.call(Input, button);
            if (button == "ALL") {
                apply();
            } else {
                const act = YEP_BCE_switch_map[button];
                const xact = action[act];
                Object.keys(map).forEach(k => {
                    if (map[k] === act)
                        Input.keyMapper[key[k]] = xact;
                });
            }
        }
    }

    // Quxios QInput
    function setupQInput() {
        const qinput_keys = (QInput as any).keys as Record<number, string>;
        const qinput_key_map: {[k in Key]?: string} = Object_mapEntries(key, ([rkey, code]) => [rkey, "#"+qinput_keys[code]]);
        const hook_qinput: ApplyHook = kas => {
            const qinput_kas: [string, string][] = kas.map(([key, act]) => [qinput_key_map[key]??key, action[act]??act]);
            const remapped = Object_fromEntries(qinput_kas);
            const collected: Record<string, string[]> = {};
            qinput_kas.forEach(([key, act]) => {
                const qa = collected[act] ?? [];
                qa.push(key);
                collected[act] = qa;
            });
            const qkeys = ConfigManager.keys as Record<_QAction, string|string[]>;
            Object.keys(qkeys).forEach(qa => {
                const keys: string[] = collected[qa] ?? [];
                qkeys[qa].forEach((key: string) => {
                    if (!Object.prototype.hasOwnProperty.call(remapped, key))
                        keys.push(key);
                });
                qkeys[qa] = keys;
            });
        };
        hooks.push(hook_qinput);
    }

    const initialKeyMap = {};

    window.addEventListener("load", () => {
        Object.freeze(Object_assign(initialKeyMap, get()));
        apply();
        console.log("RPG MV/MZ Remap loaded.", map);
        if (typeof Imported !== "undefined") {
            if (Imported.YEP_ButtonCommonEvents !== undefined) {
                setupYEP_BCE();
            }
            if (Imported.QInput !== undefined) {
                setupQInput();
            }
        }
    });

    // ------------------------ API ---------------------------
    (window as any).Remap = Object.freeze({
        initial: initialKeyMap,
        key: key,
        action: action,
        options: options,
        map: (window as any).Proxy !== undefined
            ? new (window as any).Proxy(map, {
                set: (target, p, value, receiver) => {
                    set(p as Key, value);
                    return true;
                }
            })
            : undefined,
        get: get,
        set: set,
        add: add,
        apply: apply,
    });

})();