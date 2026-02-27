# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class WaterLevel(sequencetools.SenderSequence):
    """The water level within the first channel segment [m]."""

    NDIM: Final[Literal[1]] = 1
    NUMERIC = False
