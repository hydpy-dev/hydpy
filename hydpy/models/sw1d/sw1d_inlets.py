# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LongQ(sequencetools.InletSequence):
    """The longitudinal inflow into the first channel segment [m³/s]."""

    NDIM: Final[Literal[1]] = 1


class LatQ(sequencetools.InletSequence):
    """The lateral inflow into the first channel segment [m³/s]."""

    NDIM: Final[Literal[1]] = 1


class WaterLevel(sequencetools.InletSequence):
    """Water level [m]."""

    NDIM: Final[Literal[0]] = 0
