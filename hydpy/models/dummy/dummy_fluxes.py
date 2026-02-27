# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.FluxSequence):
    """Abfluss [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (0.0, None)
