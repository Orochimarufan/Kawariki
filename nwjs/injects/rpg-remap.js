// Key mapping. Assumes US-Keyboard
// TODO: make configurable somehow
// Ideally GUI?

(function() {

    // Typing helpers
    /** @typedef {'tab'|'shift'|'control'|'escape'|'debug'|'pageup'|'pagedown'|'up'|'left'|'down'|'right'|'ok'} _Action */
    /** @type {<T>(t: T) => T} */
    var id = function(o) {
        return o;
    };
    /** @type {<T>(et: { [K in keyof T]: number }) => et} */
    var _key = id;
    /** @type {<T>(et: { [K in keyof T]: _Action }) => et} */
    var _action = id;

    // Constants
    var key = _key({
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

    var action = _action({
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

    /**
     * Initial Keymap Customizations
     * @type {{[P in keyof key]?: keyof action}}
     */
    var map = {
        w: 'up',
        a: 'left',
        s: 'down',
        d: 'right',
        e: 'confirm',
        q: 'cancel',
    };

    var options = {
        overrideBCE: false,
    };

    // Code
    /**
     * @template K
     * @template V
     * @template RK
     * @template RV
     * @type {(obj: Record<K, V>, fn: (entry: [K, V]) => [RK, RV]) => Record<RK, RV>}
     */
    var mapEntries = Object.fromEntries !== undefined ?
        function mapEntries(obj, fn) {
            return Object.fromEntries(Object.entries(obj).map(fn));
        } :
        function mapEntries(obj, fn) {
            /** @type {Record<RK, RV>} */
            var newobj = {};
            Object.keys(obj).forEach(function(k) {
                entry = fn([k, obj[k]]);
                newobj[entry[0]] = entry[1];
            });
            return newobj;
        };

    /** @type {Record<number, keyof key>} */
    var keyByCode = mapEntries(key, function(kv) {
        return [kv[1], kv[0]];
    });

    /**
     * Set a single key mapping
     * @param {keyof key} keyname 
     * @param {keyof action|string} act 
     * @returns {void}
     */
    function set(keyname, act) {
        map[keyname] = act;
        var ai = action[act];
        Input.keyMapper[key[keyname]] = ai !== undefined ? ai : act;
    }

    /**
     * Get complete map including game/core definitions
     * @returns {Record<keyof key, keyof action>}
     */
    function get() {
        return mapEntries(Input.keyMapper, function(entry) {
            var k = keyByCode[entry[0]];
            return [k !== undefined ? k : entry[0], entry[1]];
        });
    }

    /**
     * Add new mappings
     * @param {Record<keyof key, keyof action|string>} mappings
     * @returns {void}
     */
    function add(mappings) {
        Object.keys(mappings).forEach(function(k) {
            set(k, mappings[k]);
        });
    }

    /**
     * Re-Apply custom mappings
     * @returns {void}
     */
    function apply() {
        Object.keys(map).forEach(function(k) {
            var an = map[k];
            var ai = action[an];
            Input.keyMapper[key[k]] = ai !== undefined ? ai : an;
        });
    }

    // Yanfly ButtonCommonEvents support
    function setupYEP_BCE() {
        /** @type {Record<string, _Action>} */
        var YEP_BCE_switch_map = {
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

        /** @type {{[K in keyof key]?: string}} */
        var YEP_BCE_key_map = {
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
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'].forEach(function(n) {
            YEP_BCE_key_map["k" + n] = n;
            YEP_BCE_key_map["n" + n] = "num" + n;
        });
        ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'].forEach(function(s) {
            YEP_BCE_key_map[s] = s;
        });

        var _switchButton = Input._switchButton;
        Input._switchButton = function(button) {
            _switchButton.call(Input, button);
            if (options.overrideBCE) {
                apply();
            } else if (button === 'ALL') {
                Object.keys(YEP_BCE_key_map).forEach(function(k) {
                    var y = YEP_BCE_key_map[k];
                    if (Yanfly.Param.BCEList[y] !== 0)
                        Input.keyMapper[key[k]] = y;
                });
            } else {
                var act = YEP_BCE_switch_map[button];
                Object.keys(map).forEach(function(k) {
                    if (map[k] === act) {
                        var y = YEP_BCE_key_map[k];
                        if (Yanfly.Param.BCEList[y] !== 0)
                            Input.keyMapper[key[k]] = y;
                    }
                });
            }
        };

        var _revertButton = Input._revertButton;
        Input._revertButton = function(button) {
            _revertButton.call(Input, button);
            if (button == "ALL") {
                apply();
            } else {
                var act = YEP_BCE_switch_map[button];
                var xact = action[act];
                Object.keys(map).forEach(function(k) {
                    if (map[k] === act) {
                        Input.keyMapper[key[k]] = xact;
                    }
                });
            }
        }
    };

    const initialKeyMap = {};

    window.addEventListener("load", function() {
        Object.freeze(Object.assign(initialKeyMap, get()));
        apply(map);
        console.log("RPG MV/MZ Remap loaded.", map);
        if (typeof Imported !== "undefined" && Imported.YEP_ButtonCommonEvents !== undefined) {
            setupYEP_BCE();
        }
    });

    window.Remap = Object.freeze({
        initial: initialKeyMap,
        key: key,
        action: action,
        options: options,
        map: new Proxy(map, {
            set: function(target, p, value, receiver) {
                set(p, value);
            }
        }),
        get: get,
        set: set,
        add: add,
        apply: apply,
    });

})();