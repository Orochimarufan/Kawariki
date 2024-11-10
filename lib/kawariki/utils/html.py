from collections.abc import Mapping
from html import escape
from html.parser import HTMLParser
from typing import IO
from warnings import warn


AttrList = list[tuple[str, str|None]]
Attrs = Mapping[str, str|None] | AttrList

Indent = int|bool
EndLine = str|bool

RAWISH_TAGS = {'script', 'style'}
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
             'link', 'meta', 'param', 'source', 'track', 'wbr'}


class HTMLBuilder:
    indentation = 4

    file: IO[str]
    stack: list[str]
    _lineoffset: int

    def __init__(self, file: IO[str]):
        self.file = file
        self.stack = []
        self._lineoffset = 0

    # Introspection
    @property
    def current_tag(self) -> str:
        """ The tag that is enclosing the current position. Empty for root. """
        try:
            return self.stack[-1]
        except IndexError:
            return ""

    @property
    def current_depth(self) -> int:
        return len(self.stack)

    @property
    def indent_prefix(self) -> str:
        return ' ' * self.indentation * self.current_depth

    # Output
    def write(self, html: str, *, indent: Indent=True, end: EndLine|None=None):
        """ Write raw html to the output file. Caller is responsible for well-fomedness

        :param html: The HTML source to write
        :param indent: Indent all lines to the current DOM level. Can be an int that is added to the level
        :param end: Append a newline to the source. Can be None to detect existing trailing newline. Can be a str.
        """
        end = (('\n' if not html.endswith('\n') else '') if end is None else
                '\n' if end is True else
                '' if end is False else
                end)
        if indent is False:
            self.file.write(html + end)
            self._lineoffset = len(html.rsplit('\n', 1)[-1]) if not end else 0
        else:
            indent_count = self.indentation * (self.current_depth + (0 if indent is True else indent))
            lines = html.split('\n')
            self.file.write(
                (' ' * (indent_count - self._lineoffset))
                + ('\n' + ' ' * indent_count).join(lines)
                + end)
            self._lineoffset = len(lines[-1]) if not end else 0

    def begin(self, tag: str, attrs: Attrs=[], *, indent: Indent=True, end: EndLine=True):
        """ Write an opening tag

        :param tag: The tag name
        :param attrs: The HTML attributes. Keys starting with '$' are ignored
        :param indent: See write()
        :param end: See write()
        """
        if attrs:
            attrpairs = attrs if isinstance(attrs, list) else attrs.items()
            attrgen = (f'{name}="{escape(value, quote=True)}"' if value is not None else name
                            for name, value in attrpairs
                            if name[0] != '$')
            self.write(f"<{tag} {' '.join(attrgen)}>", indent=indent, end=end)
        else:
            self.write(f"<{tag}>", indent=indent, end=end)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def end(self, tag: str|None=None, *, indent: Indent=True, end: EndLine=True):
        """ Write a closing tag

        :param tag: The tag name. Defaults to the innermost tag. Must not be a void element
        :param indent: See write()
        :param end: See write()
        """
        tip = self.stack.pop()
        if tag is None:
            tag = tip
        elif tag != tip:
            if tag in VOID_TAGS:
                warn(f"Ignoring attempt to output closing tag for void element {tag}")
                self.stack.append(tag)
                return
            warn(f"Outputting malformed HTML: closing {tag} while {tip} is innermost open tag")
        self.write(f"</{tag}>", indent=indent, end=end)

    def data(self, data: str, *, indent: Indent=True, end: EndLine|None=None):
        """ Like write() but escapes special HTML characters """
        need_escape = self.current_tag not in RAWISH_TAGS
        self.write(escape(data) if need_escape else data, indent=indent, end=end)

    def leaf(self, tag: str, attrs: Attrs, text: str="", *,
                indent: Indent=True, end: EndLine=True, multiline: bool|None=None):
        """ Write a leaf element. Can include text content. """
        void = tag in VOID_TAGS
        if multiline is None:
            multiline = end is True or end is None or end is not False and '\n' in end
            multiline = not void and multiline and '\n' in text
        self.begin(tag, attrs, indent=indent, end=end if void else multiline)
        if not void:
            if text:
                self.data(text, indent=indent if multiline else False, end=None if multiline else False)
            self.end(tag, indent=indent if multiline else False, end=end)
        elif text:
            warn(f"Ignored passed text content for void element {tag}")

    def comment(self, text: str, *, indent: Indent=True, end: EndLine=True):
        self.write(f"<!-- {escape(text)} -->", indent=indent, end=end)


class HTMLPatcher(HTMLParser):
    """ Modifying HTMLParser base. Passes through markup unchanged """
    stack: list[str]
    output: HTMLBuilder

    def __init__(self, output: HTMLBuilder):
        super().__init__(convert_charrefs=True)
        self.output = output
        self.stack = []

    # State
    @property
    def current_tag(self) -> str:
        """ The innermost tag that is currently being parsed """
        try:
            return self.stack[-1]
        except IndexError:
            return ""

    @property
    def current_depth(self) -> int:
        return len(self.stack)

    # Forwarding extension points
    def forward_starttag(self, tag: str, attrs: AttrList):
        self.output.begin(tag, attrs, indent=False, end=False)

    def forward_endtag(self, tag: str):
        self.output.end(tag, indent=False, end=False)

    # Handlers
    def handle_starttag(self, tag: str, attrs: AttrList):
        """ Override forward_starttag instead of this """
        self.forward_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str):
        """ Override forward_endtag instead of this """
        if tag in VOID_TAGS:
            warn(f"Malformed HTML: Ignoring closing tag to void element {tag}")
            return
        expected = self.stack.pop()
        if tag != expected:
            warn(f"Malformed HTML: Expected to close {expected} but found {tag}")
        self.forward_endtag(tag)

    def handle_data(self, data: str):
        self.output.data(data, indent=False, end=False)

    def handle_comment(self, data: str):
        self.output.write(f"<!--{escape(data)}-->", end=False)

    def handle_decl(self, decl: str):
        self.output.write(f"<!{decl}>", end=False)

    def handle_pi(self, data: str):
        self.output.write(f"<?{data}>", end=False)


class HTMLScriptsPatcher(HTMLPatcher):
    """ Collect all script tags and move them to the end of <body> """

    scripts: list[dict[str, str|None]]

    def __init__(self, output: HTMLBuilder):
        super().__init__(output)
        self.scripts = []

    @property
    def current_script(self) -> dict[str, str|None]|None:
        return self.scripts[-1] if self.current_tag == 'script' else None

    def forward_starttag(self, tag: str, attrs: AttrList):
        if tag == 'script':
            self.scripts.append(dict(attrs))
        else:
            super().forward_starttag(tag, attrs)

    def forward_endtag(self, tag: str):
        if tag == 'body':
            self.write_scripts(self.scripts)
        if tag != 'script':
            super().forward_endtag(tag)

    def handle_data(self, data: str):
        if (script := self.current_script) is not None:
            src = script.get("$src")
            script["$src"] = src + data if src else data
        else:
            super().handle_data(data)

    def write_scripts(self, scripts: list[dict[str, str|None]]):
        """ Called right before </body> to write out the collected scripts """
        for script in scripts:
            self.output.begin('script', script)
            if text := script.get('$src'):
                self.output.data(text)
            self.output.end('script')

