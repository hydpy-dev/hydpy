# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class S(sequencetools.StateSequence):
    """Storage content [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
    SPAN = (0.0, None)


class SV(sequencetools.StateSequence):
    """Storage content vector[mm]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = True
    SPAN = (0.0, None)
