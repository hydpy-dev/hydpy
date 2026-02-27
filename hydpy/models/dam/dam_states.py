# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class WaterVolume(sequencetools.StateSequence):
    """Water volume [million m³]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = True
