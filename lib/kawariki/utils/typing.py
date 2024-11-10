# typing backports
# Need to do an import cascade since these are special forms identified by
# their qualified import name. Typecheckers need to be able to follow along
# to the original definition in typing or typing_extensions. Any abstraction
# may obscure the origin

import sys

# typing.Self, typing.override
if sys.version_info >= (3, 11):
    from typing import Self, override
else:
    try:
        from typing_extensions import Self, override
    except ImportError:
        from typing import _SpecialForm

        @_SpecialForm # type: ignore[call-arg]
        def Self(self, parameters):
            raise TypeError()

        def override(_f): # type: ignore[misc]
            return _f
