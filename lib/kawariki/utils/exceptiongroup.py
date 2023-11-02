""" Python 3.11 ExceptionGroup-esque polyfill """

import sys

if sys.version_info >= (3, 11):
    from builtins import ExceptionGroup as ExceptionGroup
    from traceback import format_exception as format_exception

else:
    from typing import Sequence
    from traceback import format_exception as format_single_exception

    class ExceptionGroup(Exception):
        exceptions: Sequence[Exception]
        message: str

        def __init__(self, message: str, exceptions: Sequence[Exception]):
            self.message = message
            self.exceptions = exceptions

    def format_exception(e: Exception):
        if isinstance(e, ExceptionGroup):
            parts = "\n\n".join(format_single_exception(ec) for ec in e.exceptions)
            return f"{type(e).__name__}: {e.message}\n\n{parts}"
        return format_single_exception(e)
