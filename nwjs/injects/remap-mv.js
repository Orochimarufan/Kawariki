// Key mapping. Assumes US-Keyboard
// TODO: make configurable somehow
// Ideally GUI?

(function(){

var key = {
    backspace: 8, tab: 9,
    clear: 12, enter: 13,
    shift: 16, control: 17, alt: 18,
    pause: 19, caps: 20,
    esc: 27,
    space: 32,
    pageup: 33, pagedown: 34,
    end: 35, home: 36,
    left: 37, up: 38, right: 39, down: 40,
    select: 41, print: 42, execute: 43, printscreen: 44,
    insert: 45, delete: 46, help: 47,
    k0: 48, k1: 49, k2: 50, k3: 51, k4: 52, k5: 53, k6: 54, k7: 55, k8: 56, k9: 57,
    a: 65, b: 66, c: 67, d: 68, e: 69, f: 70, g: 71, h: 72, i: 73, j: 74,
    k: 75, l: 76, m: 77, n: 78, o: 79, p: 80, q: 81, r: 82, s: 83, t: 84,
    u: 85, v: 86, w: 87, x: 88, y: 89, z: 90,
    meta_left: 91, meta_right: 92, context: 93,
    n0: 96, n1: 97, n2: 98, n3: 99, n4: 100, n5: 101, n6: 102, n7: 103, n8: 104, n9: 105,
    n_mult: 106, n_add: 107, n_enter: 108, n_subtract: 109, n_point: 110, n_divide: 111,
    f1: 112, f2: 113, f3: 114, f4: 115, f5: 116, f6: 117, f7: 118, f8: 119, f9: 120, f10: 121,
    f11: 122, f12: 123, f13: 124, f14: 125, f15: 126, f16: 127, f17: 128, f18: 129, f19: 130, f20: 131,
    f21: 132, f22: 133, f23: 134, f24: 135, f25: 136, f26: 137, f27: 138, f28: 139, f29: 140, f30: 141,
    f31: 142, f32: 143,
    numlock: 144, scrolllock: 145,
    page_back: 166, page_forward: 167, page_reload: 168,
    vol_down: 174, vol_up: 175,
    semicolon: 186, equals: 187, comma: 188, dash: 189, period: 190, slash: 191, grave: 192,
    bracket_open: 219, backslash: 220, bracket_close: 221, quote: 222,
};

var action = {
    tab: 'tab', shift: 'shift', control: 'control', escape: 'escape',
    debug: 'debug',
    pageup: 'pageup', pagedown: 'pagedown',
    up: 'up', left: 'left', down: 'down', right: 'right',
    ok: 'ok', confirm: 'ok', cancel: 'escape',
};

/** @type {Record<keyof key, keyof action>} */
var map = {
    w: 'up',
    a: 'left',
    s: 'down',
    d: 'right',
    e: 'confirm',
    q: 'cancel',
};

window.addEventListener("load", function() {
    Object.keys(map).forEach(function (k) {
        Input.keyMapper[key[k]] = action[map[k]];
    });
    console.log("Remap-MV loaded.", map);
});

})();
