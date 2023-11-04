# Extended version of stdlib textwrap.dedent and textwrap.indent

import re

_whitespace_only_re = re.compile('^[ \t]+$', re.MULTILINE)
_leading_whitespace_re = re.compile('(^[ \t]*)(?:[^ \t\n])', re.MULTILINE)


def dedent(text: str, prefix: str='') -> str:
    """Remove any common leading whitespace from every line in `text`.

    This can be used to make triple-quoted strings line up with the left
    edge of the display, while still presenting them in the source code
    in indented form.

    Note that tabs and spaces are both treated as whitespace, but they
    are not equal: the lines "  hello" and "\\thello" are
    considered to have no common leading whitespace.

    The 'prefix' argument is added as new common indentation if given,
    such that the text is aligned at that indent

    Entirely blank lines are normalized to a newline character.
    """
    # Look for the longest leading string of spaces and tabs common to
    # all lines.
    margin = None
    text = _whitespace_only_re.sub('', text)
    indents = _leading_whitespace_re.findall(text)
    for indent in indents:
        if margin is None:
            margin = indent

        # Current line more deeply indented than previous winner:
        # no change (previous winner is still on top).
        elif indent.startswith(margin):
            pass

        # Current line consistent with and no deeper than previous winner:
        # it's the new winner.
        elif margin.startswith(indent):
            margin = indent

        # Find the largest common whitespace between current line and previous
        # winner.
        else:
            for i, (x, y) in enumerate(zip(margin, indent)):
                if x != y:
                    margin = margin[:i]
                    break

    if margin:
        text = re.sub(r'(?m)^' + margin, prefix, text)
    return text


def indent(text: str, prefix: str, *, skip_first=False, newline='\n') -> str:
    """Adds 'prefix' to the beginning of lines in 'text'.

    Trailing whitespace is always removed and newlines
    are normalized to 'newline' (default '\\n')

    If 'skip_first' is True, the first line isn't indented.
    """
    def prefixed_lines():
        it = iter(text.splitlines(False))
        if skip_first:
            yield next(it).rstrip()
        for line in it:
            line = line.rstrip()
            yield (prefix + line if line else line)
    return newline.join(prefixed_lines())
