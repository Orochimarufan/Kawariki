System.register(["$kawariki:es-polyfill", "./rpg-inject.mjs", "./logger.mjs"], function (exports_1, context_1) {
    "use strict";
    var _kawariki_es_polyfill_1, rpg_inject_mjs_1, logger_mjs_1, logger, key, action, map, plugins, keyByCode, hook_vanilla, hooks, initialKeyMap;
    var __moduleName = context_1 && context_1.id;
    function apply_keymapper(kas, mapper) {
        mapper !== null && mapper !== void 0 ? mapper : (mapper = Input.keyMapper);
        kas.forEach(function (_a) {
            var _b;
            var keyname = _a[0], act = _a[1];
            mapper[key[keyname]] = (_b = action[act]) !== null && _b !== void 0 ? _b : act;
        });
    }
    function apply(kmap) {
        if (kmap === void 0) { kmap = map; }
        var kas = _kawariki_es_polyfill_1.Object.entries(kmap);
        hooks.forEach(function (hook) { return hook(kas); });
    }
    exports_1("apply", apply);
    function set(keyname, act) {
        map[keyname] = act;
        hooks.forEach(function (hook) { return hook([[keyname, act]]); });
    }
    exports_1("set", set);
    function get(mapper) {
        mapper !== null && mapper !== void 0 ? mapper : (mapper = Input.keyMapper);
        return _kawariki_es_polyfill_1.Object.mapEntries(mapper, function (_a) {
            var code = _a[0], coreAction = _a[1];
            var k = keyByCode[code];
            return [k !== undefined ? k : code, coreAction];
        });
    }
    exports_1("get", get);
    function add(mappings) {
        _kawariki_es_polyfill_1.Object.assign(map, mappings);
        apply(mappings);
    }
    exports_1("add", add);
    function setupYEP_BCE() {
        logger.log("Detected Yanfly ButtonCommonEvents plugin");
        plugins.ButtonCommonEvents = {
            override: false,
        };
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
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'].forEach(function (n) {
            YEP_BCE_key_map["k" + n] = n;
            YEP_BCE_key_map["n" + n] = "num" + n;
        });
        ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'].forEach(function (s) {
            YEP_BCE_key_map[s] = s;
        });
        var _switchButton = Input._switchButton;
        Input._switchButton = function (button) {
            _switchButton.call(Input, button);
            if (plugins.ButtonCommonEvents.override) {
                apply();
            }
            else if (button === 'ALL') {
                Object.keys(YEP_BCE_key_map).forEach(function (k) {
                    var y = YEP_BCE_key_map[k];
                    if (Yanfly.Param.BCEList[y] !== 0)
                        Input.keyMapper[key[k]] = y;
                });
            }
            else {
                var act_1 = YEP_BCE_switch_map[button];
                Object.keys(map).forEach(function (k) {
                    if (map[k] === act_1) {
                        var y = YEP_BCE_key_map[k];
                        if (Yanfly.Param.BCEList[y] !== 0)
                            Input.keyMapper[key[k]] = y;
                    }
                });
            }
        };
        var _revertButton = Input._revertButton;
        Input._revertButton = function (button) {
            _revertButton.call(Input, button);
            if (button == "ALL") {
                apply();
            }
            else {
                var act_2 = YEP_BCE_switch_map[button];
                var xact_1 = action[act_2];
                Object.keys(map).forEach(function (k) {
                    if (map[k] === act_2)
                        Input.keyMapper[key[k]] = xact_1;
                });
            }
        };
        apply();
    }
    function setupYEP_KeyConf() {
        logger.log("Detected Yanfly Keyboard Config plugin");
        var p = plugins.KeyboardConfig = {
            initialMap: Object.freeze(get(ConfigManager.keyMapper)),
            initialWasd: Object.freeze(get(ConfigManager.wasdMap)),
        };
        apply_keymapper(_kawariki_es_polyfill_1.Object.entries(map), ConfigManager.wasdMap);
        ConfigManager.readKeyConfig = function (config, name) { var _a; return (_a = config[name]) !== null && _a !== void 0 ? _a : _kawariki_es_polyfill_1.Object.assign({}, ConfigManager.wasdMap); };
        _kawariki_es_polyfill_1.Array.removeInPlace(hooks, hook_vanilla);
    }
    function setupQInput() {
        logger.log("Detected QInput plugin");
        var qinput_keys = QInput.keys;
        var qinput_key_map = _kawariki_es_polyfill_1.Object.mapEntries(key, function (_a) {
            var rkey = _a[0], code = _a[1];
            return [rkey, "#" + qinput_keys[code]];
        });
        var hook_qinput = function (kas) {
            var qinput_kas = kas.map(function (_a) {
                var _b, _c;
                var key = _a[0], act = _a[1];
                return [(_b = qinput_key_map[key]) !== null && _b !== void 0 ? _b : key, (_c = action[act]) !== null && _c !== void 0 ? _c : act];
            });
            var remapped = _kawariki_es_polyfill_1.Object.fromEntries(qinput_kas);
            var collected = {};
            qinput_kas.forEach(function (_a) {
                var _b;
                var key = _a[0], act = _a[1];
                var qa = (_b = collected[act]) !== null && _b !== void 0 ? _b : [];
                qa.push(key);
                collected[act] = qa;
            });
            var qkeys = ConfigManager.keys;
            Object.keys(qkeys).forEach(function (qa) {
                var _a;
                var keys = (_a = collected[qa]) !== null && _a !== void 0 ? _a : [];
                qkeys[qa].forEach(function (key) {
                    if (!Object.prototype.hasOwnProperty.call(remapped, key))
                        keys.push(key);
                });
                qkeys[qa] = keys;
            });
        };
        hooks.push(hook_qinput);
        apply();
    }
    return {
        setters: [
            function (_kawariki_es_polyfill_1_1) {
                _kawariki_es_polyfill_1 = _kawariki_es_polyfill_1_1;
            },
            function (rpg_inject_mjs_1_1) {
                rpg_inject_mjs_1 = rpg_inject_mjs_1_1;
            },
            function (logger_mjs_1_1) {
                logger_mjs_1 = logger_mjs_1_1;
            }
        ],
        execute: function () {
            logger = new logger_mjs_1.Logger("RpgRemap", { color: "DarkGreen" });
            exports_1("key", key = {
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
            exports_1("action", action = {
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
            map = {
                w: 'up',
                a: 'left',
                s: 'down',
                d: 'right',
                e: 'confirm',
                q: 'cancel',
                r: 'pageup',
                f: 'pagedown',
            };
            exports_1("plugins", plugins = {});
            exports_1("keyByCode", keyByCode = _kawariki_es_polyfill_1.Object.mapEntries(key, function (_a) {
                var key = _a[0], code = _a[1];
                return [code, key];
            }));
            hook_vanilla = apply_keymapper;
            hooks = [hook_vanilla];
            initialKeyMap = {};
            rpg_inject_mjs_1.inject.on("boot", function () {
                Object.freeze(_kawariki_es_polyfill_1.Object.assign(initialKeyMap, get()));
                (function () {
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
                key: key,
                action: action,
                plugins: plugins,
                map: window.Proxy !== undefined
                    ? new window.Proxy(map, {
                        set: function (target, p, value, receiver) {
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
        }
    };
});
//# sourceMappingURL=rpg-remap.mjs.map