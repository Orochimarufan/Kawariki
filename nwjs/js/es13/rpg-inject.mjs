import { Logger } from "./logger.mjs";
import { Array as _Array, String as _String } from '$kawariki:es-polyfill';
function isElement(node) {
    return node.nodeType === node.ELEMENT_NODE;
}
function isScriptElement(node) {
    return isElement(node) && node.tagName === "SCRIPT";
}
export class Injector {
    static defaultScripts = [
        ['js/plugins.js', 'plugins'],
        ['js/main.js', 'main'],
        ['js/rpg_core.js', 'core'],
        ['js/rpg_managers.js', 'managers'],
        ['js/rmmz_core.js', 'core'],
        ['js/rmmz_managers.js', 'managers'],
    ];
    static fixedEvents = [
        'script-added',
        'script-loaded',
        'plugins-setup',
        'plugins-loaded',
        'plugin-setup',
        'plugin-loaded',
        'boot',
    ];
    observer;
    scripts;
    events;
    listeners;
    logger;
    log_event;
    dispatch(names, detail) {
        const prefix = names[0]?.slice(0, 7);
        if (names.length !== 1 || (prefix !== 'script-' && prefix !== 'plugin-'))
            this.log_event(names, detail);
        for (const name of names) {
            for (const lner of this.listeners[name] ?? []) {
                lner(detail, this);
            }
        }
    }
    static scriptEventName(scriptname, type) {
        return `script-${scriptname}-${type}`;
    }
    constructor() {
        this.logger = new Logger("RpgInject", { color: "MediumPurple" });
        this.log_event = this.logger.makeLogFn('info', 'Triggered %s: %o');
        this.listeners = {};
        const se = Injector.scriptEventName;
        this.scripts = Injector.defaultScripts.concat();
        this.events = Injector.fixedEvents.concat(_Array.flatMap(_Array.unique(this.scripts.map(([_, k]) => k)), name => [se(name, 'added'), se(name, 'loaded')]));
        this.observer = new MutationObserver((mutations) => {
            for (const m of mutations) {
                m.addedNodes.forEach(e => {
                    if (isScriptElement(e)) {
                        const detail = { script: e };
                        const events_added = ['script-added'];
                        const events_loaded = ['script-loaded'];
                        if (e.src !== '') {
                            const src = new URL(e.src);
                            for (const [scriptname, eventname] of this.scripts) {
                                if (_String.endsWith(src.pathname, scriptname)) {
                                    events_added.push(se(eventname, 'added'));
                                    events_loaded.push(se(eventname, 'loaded'));
                                }
                            }
                        }
                        this.dispatch(events_added, detail);
                        e.addEventListener('load', this.dispatch.bind(this, events_loaded, detail));
                    }
                });
            }
        });
        document.addEventListener("DOMContentLoaded", this.observer.disconnect.bind(this.observer));
        this.observer.observe(document, {
            childList: true,
            subtree: true,
        });
        this.on('script-managers-loaded', detail => {
            const self = this;
            if (Utils.RPGMAKER_NAME === "MV") {
                PluginManager.setup = function (plugins) {
                    self.dispatch(['plugins-setup'], { plugins });
                    for (const plugin of plugins) {
                        if (plugin.status && !_Array.includes(this._scripts, plugin.name)) {
                            plugin._filename = plugin.name + ".js";
                            self.dispatch(['plugin-setup'], { plugin });
                            this.setParameters(plugin.name, plugin.parameters);
                            this.loadScript(plugin._filename);
                            this._scripts.push(plugin.name);
                            self.dispatch(['plugin-loaded'], { plugin });
                        }
                    }
                    self.dispatch(['plugins-loaded'], { plugins });
                };
            }
            else {
                PluginManager.setup = function (plugins) {
                    self.dispatch(['plugins-setup'], { plugins });
                    for (const plugin of plugins) {
                        plugin._filename = Utils.extractFileName(plugin.name);
                        if (plugin.status && !_Array.includes(this._scripts, plugin._filename)) {
                            self.dispatch(['plugin-setup'], { plugin });
                            this.setParameters(plugin.name, plugin.parameters);
                            this.loadScript(plugin._filename);
                            this._scripts.push(plugin.name);
                            self.dispatch(['plugin-loaded'], { plugin });
                        }
                    }
                    self.dispatch(['plugins-loaded'], { plugins });
                };
            }
        });
        this.on('plugins-loaded', detail => {
            const _run = SceneManager.run;
            const self = this;
            SceneManager.run = function (scene) {
                self.dispatch(['boot'], {});
                _run.call(this, scene);
            };
        });
    }
    get eventNames() {
        return this.events;
    }
    observeScript(scriptsrc, eventprefix) {
        this.scripts.push([scriptsrc, eventprefix]);
        const events = [Injector.scriptEventName(eventprefix, 'added'), Injector.scriptEventName(eventprefix, 'loaded')];
        this.events.push.apply(this.events, events);
        return events;
    }
    on(type, callback) {
        const lners = this.listeners[type];
        if (lners === undefined)
            this.listeners[type] = [callback];
        else
            lners.push(callback);
    }
}
export const inject = new Injector();
//# sourceMappingURL=rpg-inject.mjs.map