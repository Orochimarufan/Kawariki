//  --------------------- Fancy Console Logger --------------------------------
export type LogLevel = 'log'|'debug'|'trace'|'info'|'warn'|'error';
export type LogFunction = (...data: any[]) => void;

export class Logger {
    private name: string;
    private color: string;
    private console: Console;

    static DEFAULT_COLORS = [
        "maroon", "purple", "fuchsia", "green", "lime", "olive", "navy", "blue", "teal", "aqua",
        "aquamarine", "bisque", "blueviolet", "brown", "cadetblue", "chocolate", "coral", "cornflowerblue", "crimson",
        "darkblue", "darkcyan", "darkgoldenrod", "darkgrey", "darkgreen", "darkkhaki", "darkmagenta", "darkolivegreen", "darkorchid",
        "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategrey", "darkviolet", "deeppink", "deepskyblue",
        "dodgerblue", "firebrick", "forestgreen", "fuchsia", "hotpink", "indianred", "indigo", "limegreen",
        "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen",
        "mediumturquoise", "mediumvioletred", "midnightblue", "olive", "orange", "orangered", "orchid", "plum", "rebeccapurple",
        "royalblue", "saddlebrown", "seagreen", "sienna", "slateblue", "steelblue", "tomato"
    ];

    constructor(name: string, options?: {color?: string, console?: Console}) {
        this.name = name;
        this.color = options?.color ?? Logger.DEFAULT_COLORS[(this.idhash & 0xFFFF) % Logger.DEFAULT_COLORS.length];
        this.console = options?.console ?? window.console;
    }

    protected get idhash(): number {
        // https://stackoverflow.com/a/52171480
        const s = this.name;
        for(var i=0,h=9;i<s.length;)
            h=Math.imul(h^s.charCodeAt(i++),9**9);
        return h^h>>>9;
    }

    protected get prefix_fmt() {
        return '%c%s%c';
    }

    protected get prefix_fparams() {
        return [
            `background-color: ${this.color}; color: white; padding: 0.1rem 0.25rem; border-radius: 4px;`,
            this.name,
            `background-color: default; color: default; padding: default; border-radius: 0;`
        ];
    }

    makeLogFn(level: LogLevel, fmt?: string, ...data: any[]): LogFunction {
        const fn = this.console[level];
        const xfmt = fmt ? `${this.prefix_fmt} ${fmt}` : this.prefix_fmt;
        return fn.bind.apply(fn, [this.console, xfmt].concat(this.prefix_fparams, data));
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
