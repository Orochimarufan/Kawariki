// ============================================================================
// Tools for injecting into RPGMaker initialization at different points

import { Logger } from "./logger.mjs";
import { Object as _Object, Array as _Array, String as _String } from '$kawariki:es-polyfill';

// -------------------------- Injection Points ----------------------
export type InjectWhen = 'before'|'after';
type FixedScriptEventName = 'script-added'|'script-loaded';
type PluginsEventName = 'plugins-setup'|'plugins-loaded';
type PluginEventName = 'plugin-setup'|'plugin-loaded';
type VoidEventName = 'boot';
export type FixedEventName = FixedScriptEventName | PluginsEventName | PluginEventName | VoidEventName;

type ScriptEventTypeName = 'added' | 'loaded';
type DefaultScriptName = 'core' | 'managers' | 'plugins' | 'main';
type SpecificScriptEventName<S extends string, E extends ScriptEventTypeName=ScriptEventTypeName> = `script-${S}-${E}`;
type DefaultScriptEventName = SpecificScriptEventName<DefaultScriptName>;

export type DefaultEventName = FixedEventName | DefaultScriptEventName;

type AnyScriptEventName = SpecificScriptEventName<string>;
type ScriptEventName = FixedScriptEventName | AnyScriptEventName;
export type EventName = FixedEventName | AnyScriptEventName;

export type EventDetail<Name extends EventName> = (
    Name extends PluginsEventName ? {plugins: PluginManager_PluginDef[]} :
    Name extends PluginEventName ? {plugin: PluginManager_PluginDef} :
    Name extends VoidEventName ? {} :
    Name extends ScriptEventName ? {script: HTMLScriptElement} :
    never
);

export type EventHandler<Name extends EventName> = (detail: EventDetail<Name>, target: object) => void;

// -------------------------- DOM Helpers ---------------------------
function isElement(node: Node): node is Element {
    return node.nodeType === node.ELEMENT_NODE;
}

function isScriptElement(node: Node): node is HTMLScriptElement {
    return isElement(node) && node.tagName === "SCRIPT";
}

// -------------------------- Implementation ------------------------
export class Injector {
    private static defaultScripts: [string, DefaultScriptName][] = [
        // Common
        ['js/plugins.js', 'plugins'],
        ['js/main.js', 'main'],
        // RPGMaker MV
        ['js/rpg_core.js', 'core'],
        ['js/rpg_managers.js', 'managers'],
        // RPGMaker MZ
        ['js/rmmz_core.js', 'core'],
        ['js/rmmz_managers.js', 'managers'],
    ];
    private static fixedEvents: FixedEventName[] = [
        'script-added',     // Script added to DOM: {script: HTMLScriptElement}
        'script-loaded',    // Script element loaded: {script: HTMLScriptElement}
        // 'script-<script>-added' Like script-added but only for observed script filename
        // 'script-<script>-loaded' Like script-loaded but only for observed script filename
        'plugins-setup',    // Before setting up any plugins: {plugins: PluginDef[]}
        'plugins-loaded',   // Plugin setup done
        'plugin-setup',     // Plugin about to be initialized: {plugin: PluginDef}
        'plugin-loaded',    // Plugin finished loading: {plugin: PluginDef}
        'boot',             // Just before SceneManager.run called
    ];

    private observer: MutationObserver;
    private scripts: [string, string][];
    private events: EventName[];
    private listeners: {[Name in EventName]?: EventHandler<Name>[]};
    private logger: Logger;
    private log_event: any;

    private dispatch<N extends EventName>(names: N[], detail: EventDetail<N>): void {
        // Don't log script- and plugin- events unless the script is being observed
        const prefix = names[0]?.slice(0, 7);
        if (names.length !== 1 || (prefix !== 'script-' && prefix !== 'plugin-'))
            this.log_event(names, detail);
        for (const name of names) {
            for (const lner of this.listeners[name] ?? []) {
                lner(detail, this);
            }
        }
    }

    private static scriptEventName(scriptname: string, type: ScriptEventTypeName): AnyScriptEventName {
        return `script-${scriptname}-${type}`;
    }

    constructor() {
        this.logger = new Logger("RpgInject", {color: "MediumPurple"});
        this.log_event = this.logger.makeLogFn('info', 'Triggered %s: %o');
        this.listeners = {};
        // Build event list
        const se = Injector.scriptEventName;
        this.scripts = Injector.defaultScripts.concat();
        this.events = (Injector.fixedEvents as EventName[]).concat(_Array.flatMap(
            _Array.unique(this.scripts.map(([_, k]) => k)),
            name => [se(name, 'added'), se(name, 'loaded')]));
        // Observe DOM for scripts
        this.observer = new MutationObserver((mutations) => {
            for (const m of mutations) {
                m.addedNodes.forEach(e => {
                    if (isScriptElement(e)) {
                        const detail = {script: e};
                        const events_added: ScriptEventName[] = ['script-added'];
                        const events_loaded: ScriptEventName[] = ['script-loaded'];
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
        // Patch PluginManager.setup()
        this.on('script-managers-loaded', detail => {
            const self = this;
            const extractFileName = 
                  Utils.RPGMAKER_NAME === "MV"
                ? name => name + ".js"
                : Utils.extractFileName !== undefined
                ? Utils.extractFileName.bind(Utils)
                : name => name;
            PluginManager.setup = function(this: typeof PluginManager, plugins) {
                self.dispatch(['plugins-setup'], {plugins});
                for (const plugin of plugins) {
                    // XXX: dispatch setup even when not enabled?
                    if (plugin.status && !_Array.includes(this._scripts, plugin.name)) {
                        plugin._filename = extractFileName(plugin.name);
                        self.dispatch(['plugin-setup'], {plugin});
                        // Actually load plugin
                        this.setParameters(plugin.name, plugin.parameters);
                        this.loadScript(plugin._filename);
                        this._scripts.push(plugin.name);
                        // Done
                        self.dispatch(['plugin-loaded'], {plugin});
                    }
                }
                self.dispatch(['plugins-loaded'], {plugins});
            }
        });
        // Patch SceneManager.run()
        this.on('plugins-loaded', detail => {
            const _run = SceneManager.run;
            const self = this;
            SceneManager.run = function(scene: any) {
                self.dispatch(['boot'], {});
                _run.call(this, scene);
            };
        });
    }

    get eventNames() {
        return this.events;
    }

    observeScript(scriptsrc: string, eventprefix: string): AnyScriptEventName[] {
        this.scripts.push([scriptsrc, eventprefix]);
        const events = [Injector.scriptEventName(eventprefix, 'added'), Injector.scriptEventName(eventprefix, 'loaded')];
        this.events.push.apply(this.events, events);
        return events;
    }

    on<N extends EventName>(type: N, callback: EventHandler<N>): void {
        const lners = this.listeners[type];
        if (lners === undefined)
            (this.listeners as any)[type] = [callback];
        else
            lners.push(callback);
    }
}

export const inject = new Injector();
