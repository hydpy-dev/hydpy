# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Q(sequencetools.ReceiverSequence):
    """Discharge at the target location [m³/s]."""

    NDIM: Final[Literal[0]] = 0


class WaterVolume(sequencetools.ReceiverSequence):
    """The current water volume of the individual sources [million m³]."""

    NDIM: Final[Literal[1]] = 1
