//  --------------------- Fancy Console Logger --------------------------------
export type LogLevel = 'log'|'debug'|'trace'|'info'|'warn'|'error';
export type LogFunction = (...data: any[]) => void;

export class Logger {
    private name: string;
    private color: string;
    private console: Console;

    constructor(name: string, options?: {color?: string, console?: Console}) {
        this.name = name;
        this.color = options?.color ?? 'SeaGreen';
        this.console = options?.console ?? window.console;
    }

    protected get fparams() {
        return [
            `background-color: ${this.color}; color: white; padding: 0.1rem 0.25rem; border-radius: 4px;`,
            this.name,
            `background-color: default; color: default; padding: default; border-radius: 0;`
        ];
    }

    makeLogFn(level: LogLevel, fmt?: string, ...data: any[]): LogFunction {
        const fn = this.console[level];
        const xfmt = fmt ? `%c%s%c ${fmt}` : "%c%s%c";
        return fn.bind.apply(fn, [this.console, xfmt].concat(data, this.fparams));
    }

    private makeMemoFn(level: LogLevel): LogFunction {
        // Only create simple functions once, memoize in this to shadow getter
        const fn = this.makeLogFn(level);
        Object.defineProperty(this, level, {value: fn});
        return fn;
    }

    get log() {
        return this.makeMemoFn('log');
    }

    get debug() {
        return this.makeMemoFn('debug');
    }

    get trace() {
        return this.makeMemoFn('trace');
    }

    get info() {
        return this.makeMemoFn('info');
    }

    get warn() {
        return this.makeMemoFn('warn');
    }

    get error() {
        return this.makeMemoFn('error');
    }
}
