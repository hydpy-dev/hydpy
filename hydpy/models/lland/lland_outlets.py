# pylint: disable=missing-module-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.OutletSequence):
    """Abfluss (runoff) [m³/s]."""

    NDIM: Final[Literal[0]] = 0
