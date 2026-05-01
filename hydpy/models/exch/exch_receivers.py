# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class WaterLevel(sequencetools.ReceiverSequence):
    """The water level at a single remote location [m]."""

    NDIM: Final[Literal[0]] = 0


class WaterLevels(sequencetools.ReceiverSequence):
    """The water level at multiple remote locations [m]."""

    NDIM: Final[Literal[1]] = 1
