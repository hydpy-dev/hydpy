# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.InletSequence):
    """Runoff [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
