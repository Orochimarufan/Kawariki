export class Logger {
    name;
    color;
    console;
    constructor(name, options) {
        this.name = name;
        this.color = options?.color ?? 'SeaGreen';
        this.console = options?.console ?? window.console;
    }
    get prefix_fmt() {
        return '%c%s%c';
    }
    get prefix_fparams() {
        return [
            `background-color: ${this.color}; color: white; padding: 0.1rem 0.25rem; border-radius: 4px;`,
            this.name,
            `background-color: default; color: default; padding: default; border-radius: 0;`
        ];
    }
    makeLogFn(level, fmt, ...data) {
        const fn = this.console[level];
        const xfmt = fmt ? `${this.prefix_fmt} ${fmt}` : this.prefix_fmt;
        return fn.bind.apply(fn, [this.console, xfmt].concat(this.prefix_fparams, data));
    }
    makeMemoFn(level) {
        const fn = this.makeLogFn(level);
        Object.defineProperty(this, level, { value: fn });
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
//# sourceMappingURL=logger.mjs.map