export type ScriptEvent = "add"|"load"|"error";
export type ScriptEventHandler = (event: ScriptEvent, script: HTMLScriptElement) => void;
export type GlobalEvent = "settled";
export type GlobalEventHandler = (event: GlobalEvent) => void;
export type Event = ScriptEvent|GlobalEvent;
export type EventHandlerFor<E extends Event> = E extends ScriptEvent ? ScriptEventHandler : 
                                               E extends GlobalEvent ? GlobalEventHandler :
                                               never;


export class ScriptObserver {
    private _active: boolean;
    private _pending: number;
    private _errors: number;
    private _count: number;
    private _observer: MutationObserver;
    private _listeners: {[E in Event]: EventHandlerFor<E>[]};

    constructor() {
        this._active = false;
        this._pending = 0;
        this._errors = 0;
        this._count = 0;
        this._listeners = {"add": [], "load": [], "error": [], "settled": []};
        this._observer = new MutationObserver(mutations => {
            for (const m of mutations) {
                m.addedNodes.forEach(e => {
                    if (e.nodeName === "SCRIPT") {
                        this._dispatch(e as HTMLScriptElement, "add");
                        e.addEventListener("load", this._dispatch.bind(this, e, "load"));
                        e.addEventListener("error", this._dispatch.bind(this, e, "error"));
                    }
                });
            }
        });
    }

    private _dispatch(script: HTMLScriptElement, event: ScriptEvent) {
        if (event === "add") {
            this._pending += 1;
            this._count += 1;
        } else {
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

    on<E extends Event>(event: E, listener: EventHandlerFor<E>): EventHandlerFor<E>;
    on<E extends Event>(events: E[], listener: EventHandlerFor<E>): EventHandlerFor<E>;
    on<E extends Event>(events: E|E[], listener: EventHandlerFor<E>): EventHandlerFor<E> {
        if (!Array.isArray(events))
            events = [events];
        for (const event of events)
            this._listeners[event].push(listener);
        return listener;
    }

    off<E extends Event>(event: E, listener: EventHandlerFor<E>): void;
    off<E extends Event>(events: E[], listener: EventHandlerFor<E>): void;
    off(events: null, listener: ScriptEventHandler|GlobalEventHandler): void;
    off(events: Event|Event[]|null, listener: any): void {
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

    get pending(): number {
        return this._pending;
    }

    get errors(): number {
        return this._errors;
    }

    get count(): number {
        return this._count;
    }

    get active(): boolean {
        return this._active;
    }

    get settled(): boolean {
        return this._pending < 1;
    }
}


let GLOBAL: ScriptObserver | null = null;

export function global(): ScriptObserver {
    if (GLOBAL === null) {
        GLOBAL = new ScriptObserver();
        GLOBAL.observe();
    }
    return GLOBAL;
}
