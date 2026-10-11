# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.kinw import kinw_variables


class WaterDepth(kinw_variables.MixinSegments, sequencetools.FactorSequence):
    """Water depth [m]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)
