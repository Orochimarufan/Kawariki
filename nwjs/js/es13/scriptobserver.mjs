export class ScriptObserver {
    _active;
    _pending;
    _errors;
    _count;
    _observer;
    _listeners;
    constructor() {
        this._active = false;
        this._pending = 0;
        this._errors = 0;
        this._count = 0;
        this._listeners = { "add": [], "load": [], "error": [], "settled": [] };
        this._observer = new MutationObserver(mutations => {
            for (const m of mutations) {
                m.addedNodes.forEach(e => {
                    if (e.nodeName === "SCRIPT") {
                        this._dispatch(e, "add");
                        e.addEventListener("load", this._dispatch.bind(this, e, "load"));
                        e.addEventListener("error", this._dispatch.bind(this, e, "error"));
                    }
                });
            }
        });
    }
    _dispatch(script, event) {
        if (event === "add") {
            this._pending += 1;
            this._count += 1;
        }
        else {
            this._pending -= 1;
            if (event === "error")
                this._errors += 1;
        }
        for (const l of this._listeners[event])
            l(event, script);
        if (this._pending < 1) {
            for (const l of this._listeners.settled)
                l("settled");
        }
    }
    observe() {
        this._active = true;
        this._pending = 0;
        this._errors = 0;
        this._count = 0;
        this._observer.observe(document, {
            childList: true,
            subtree: true,
        });
    }
    disconnect() {
        this._observer.disconnect();
        this._active = false;
    }
    on(events, listener) {
        if (!Array.isArray(events))
            events = [events];
        for (const event of events)
            this._listeners[event].push(listener);
        return listener;
    }
    off(events, listener) {
        if (events === null)
            events = ["add", "error", "load", "settled"];
        else if (!Array.isArray(events))
            events = [events];
        for (const event of events) {
            const i = this._listeners[event].indexOf(listener);
            if (i >= 0)
                this._listeners[event].splice(i, 1);
        }
    }
    get pending() {
        return this._pending;
    }
    get errors() {
        return this._errors;
    }
    get count() {
        return this._count;
    }
    get active() {
        return this._active;
    }
    get settled() {
        return this._pending < 1;
    }
}
let GLOBAL = null;
export function global() {
    if (GLOBAL === null) {
        GLOBAL = new ScriptObserver();
        GLOBAL.observe();
    }
    return GLOBAL;
}
//# sourceMappingURL=scriptobserver.mjs.map