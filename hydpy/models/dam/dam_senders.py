# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class D(sequencetools.SenderSequence):
    """Water demand [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class S(sequencetools.SenderSequence):
    """Required water supply [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class R(sequencetools.SenderSequence):
    """Required water relief [m³/s]."""

    NDIM: Final[Literal[0]] = 0
