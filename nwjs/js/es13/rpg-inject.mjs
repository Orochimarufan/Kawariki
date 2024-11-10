import { Logger } from "./logger.mjs";
import { Array as _Array, String as _String } from '$kawariki:es-polyfill';
import { global } from './scriptobserver.mjs';
export class Injector {
    static defaultScripts = [
        ['js/plugins.js', 'plugins'],
        ['js/main.js', 'main'],
        ['js/rpg_core.js', 'core'],
        ['js/rpg_managers.js', 'managers'],
        ['js/rpg_objects.js', 'objects'],
        ['js/rmmz_core.js', 'core'],
        ['js/rmmz_managers.js', 'managers'],
        ['js/rmmz_objects.js', 'objects'],
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
    constructor(observer) {
        this.logger = new Logger("RpgInject", { color: "MediumPurple" });
        this.log_event = this.logger.makeLogFn('debug', 'Triggered %s: %o');
        this.listeners = {};
        const se = Injector.scriptEventName;
        this.scripts = Injector.defaultScripts.concat();
        this.events = Injector.fixedEvents.concat(_Array.flatMap(_Array.unique(this.scripts.map(([_, k]) => k)), name => [se(name, 'added'), se(name, 'loaded')]));
        this.observer = observer;
        this.observer.on('add', (_, script) => {
            const detail = { script };
            const events_added = ['script-added'];
            const events_loaded = ['script-loaded'];
            if (script.src !== '') {
                const src = new URL(script.src);
                for (const [scriptname, eventname] of this.scripts) {
                    if (_String.endsWith(src.pathname, scriptname)) {
                        events_added.push(se(eventname, 'added'));
                        events_loaded.push(se(eventname, 'loaded'));
                    }
                }
            }
            this.dispatch(events_added, detail);
            script.addEventListener('load', this.dispatch.bind(this, events_loaded, detail));
        });
        this.on('script-managers-loaded', detail => {
            const self = this;
            const isMV = Utils.RPGMAKER_NAME === "MV";
            const extractFileName = Utils.RPGMAKER_NAME === "MZ" && Utils.extractFileName !== undefined
                ? Utils.extractFileName.bind(Utils)
                : name => name;
            PluginManager.setup = function (plugins) {
                self.dispatch(['plugins-setup'], { plugins });
                for (const plugin of plugins) {
                    const key = plugin._filename = extractFileName(plugin.name);
                    if (plugin.status && !_Array.includes(this._scripts, key)) {
                        self.dispatch(['plugin-setup'], { plugin });
                        this.setParameters(key, plugin.parameters);
                        this.loadScript(isMV ? plugin.name + ".js" : plugin.name);
                        this._scripts.push(key);
                        self.dispatch(['plugin-loaded'], { plugin });
                    }
                }
                self.dispatch(['plugins-loaded'], { plugins });
            };
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
export const inject = new Injector(global());
//# sourceMappingURL=rpg-inject.mjs.map