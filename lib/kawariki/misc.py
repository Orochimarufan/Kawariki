# :---------------------------------------------------------------------------:
#   Misc. utilities
# :---------------------------------------------------------------------------:

import os.path
import shlex
import shutil
import textwrap


def version_str(ver: tuple):
    return '.'.join(map(str, ver))

def copy_unlink(src, dst):
    # Unlink first to be able to overwrite write-protected files
    if os.path.exists(dst):
        os.unlink(dst)
    return shutil.copy2(src, dst)

def hardlink_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError as e:
        if e.errno != errno.EXDEV:
            raise
    else:
        return
    shutil.copy2(src, dst)

def format_launcher_script(*args, append_args=True):
        return textwrap.dedent(f'''\
            #!/bin/sh
            cd "`dirname "$0"`"
            exec {shlex.join(map(str, args))}{' "$@"' if append_args else ""}
            ''')


class ErrorCode(Exception):
    code: int
    def __init__(self, code: int):
        super().__init__()
        self.code = code

