# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Exchange(sequencetools.OutletSequence):
    """Bidirectional water exchange [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False


class Branched(sequencetools.OutletSequence):
    """Branched outputs [e.g. m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
