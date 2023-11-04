import { Object as _Object, Array as _Array } from "$kawariki:es-polyfill";
import { inject } from "./rpg-inject.mjs";
import { Logger } from "./logger.mjs";
const logger = new Logger("RpgRemap", { color: "DarkGreen" });
export const key = {
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
};
export const action = {
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
};
const map = {
    w: 'up',
    a: 'left',
    s: 'down',
    d: 'right',
    e: 'confirm',
    q: 'cancel',
    r: 'pageup',
    f: 'pagedown',
};
export const plugins = {};
export const keyByCode = _Object.mapEntries(key, ([key, code]) => [code, key]);
function apply_keymapper(kas, mapper) {
    mapper ??= Input.keyMapper;
    kas.forEach(([keyname, act]) => {
        mapper[key[keyname]] = action[act] ?? act;
    });
}
const hook_vanilla = apply_keymapper;
const hooks = [hook_vanilla];
export function apply(kmap = map) {
    const kas = _Object.entries(kmap);
    hooks.forEach(hook => hook(kas));
}
export function set(keyname, act) {
    map[keyname] = act;
    hooks.forEach(hook => hook([[keyname, act]]));
}
export function get(mapper) {
    mapper ??= Input.keyMapper;
    return _Object.mapEntries(mapper, ([code, coreAction]) => {
        const k = keyByCode[code];
        return [k !== undefined ? k : code, coreAction];
    });
}
export function add(mappings) {
    _Object.assign(map, mappings);
    apply(mappings);
}
function setupYEP_BCE() {
    logger.log("Detected Yanfly ButtonCommonEvents plugin");
    plugins.ButtonCommonEvents = {
        override: false,
    };
    const YEP_BCE_switch_map = {
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
    const YEP_BCE_key_map = {
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
    const _switchButton = Input._switchButton;
    Input._switchButton = (button) => {
        _switchButton.call(Input, button);
        if (plugins.ButtonCommonEvents.override) {
            apply();
        }
        else if (button === 'ALL') {
            Object.keys(YEP_BCE_key_map).forEach(k => {
                const y = YEP_BCE_key_map[k];
                if (Yanfly.Param.BCEList[y] !== 0)
                    Input.keyMapper[key[k]] = y;
            });
        }
        else {
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
    const _revertButton = Input._revertButton;
    Input._revertButton = function (button) {
        _revertButton.call(Input, button);
        if (button == "ALL") {
            apply();
        }
        else {
            const act = YEP_BCE_switch_map[button];
            const xact = action[act];
            Object.keys(map).forEach(k => {
                if (map[k] === act)
                    Input.keyMapper[key[k]] = xact;
            });
        }
    };
    apply();
}
function setupYEP_KeyConf() {
    logger.log("Detected Yanfly Keyboard Config plugin");
    const p = plugins.KeyboardConfig = {
        initialMap: Object.freeze(get(ConfigManager.keyMapper)),
        initialWasd: Object.freeze(get(ConfigManager.wasdMap)),
    };
    apply_keymapper(_Object.entries(map), ConfigManager.wasdMap);
    ConfigManager.readKeyConfig = (config, name) => config[name] ?? _Object.assign({}, ConfigManager.wasdMap);
    _Array.removeInPlace(hooks, hook_vanilla);
}
function setupQInput() {
    logger.log("Detected QInput plugin");
    const qinput_keys = QInput.keys;
    const qinput_key_map = _Object.mapEntries(key, ([rkey, code]) => [rkey, "#" + qinput_keys[code]]);
    const hook_qinput = kas => {
        const qinput_kas = kas.map(([key, act]) => [qinput_key_map[key] ?? key, action[act] ?? act]);
        const remapped = _Object.fromEntries(qinput_kas);
        const collected = {};
        qinput_kas.forEach(([key, act]) => {
            const qa = collected[act] ?? [];
            qa.push(key);
            collected[act] = qa;
        });
        const qkeys = ConfigManager.keys;
        Object.keys(qkeys).forEach(qa => {
            const keys = collected[qa] ?? [];
            qkeys[qa].forEach((key) => {
                if (!Object.prototype.hasOwnProperty.call(remapped, key))
                    keys.push(key);
            });
            qkeys[qa] = keys;
        });
    };
    hooks.push(hook_qinput);
    apply();
}
const initialKeyMap = {};
inject.on("boot", () => {
    Object.freeze(_Object.assign(initialKeyMap, get()));
    (() => {
        if (typeof Imported !== "undefined") {
            if (Imported.YEP_KeyboardConfig !== undefined) {
                return setupYEP_KeyConf();
            }
            else if (Imported.YEP_ButtonCommonEvents !== undefined) {
                return setupYEP_BCE();
            }
            else if (Imported.QInput !== undefined) {
                return setupQInput();
            }
        }
        return apply();
    })();
    logger.log("Kawariki RPG Maker MV/MZ key remapper loaded.", map);
});
window.Remap = Object.freeze({
    initial: initialKeyMap,
    key,
    action,
    plugins,
    map: window.Proxy !== undefined
        ? new window.Proxy(map, {
            set: (target, p, value, receiver) => {
                set(p, value);
                return true;
            }
        })
        : undefined,
    get: get,
    set: set,
    add: add,
    apply: apply,
});
//# sourceMappingURL=rpg-remap.mjs.map