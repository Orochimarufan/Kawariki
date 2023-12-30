# typing backports
# Need to do an import cascade since these are special forms identified by
# their qualified import name. Typecheckers need to be able to follow along
# to the original definition in typing or typing_extensions. Any abstraction
# may obscure the origin

# typing.Self
try:
    from typing import Self
except ImportError:
    try:
        from typing_extensions import Self
    except ImportError:
        from typing import _SpecialForm
        @_SpecialForm
        def Self(self, parameters):
            raise TypeError()

# typing.override
try:
    from typing import override
except ImportError:
    try:
        from typing_extensions import override
    except ImportError:
        def override(_f):
            return _f
