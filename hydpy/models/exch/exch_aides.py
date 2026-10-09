# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class EffectiveTransfer(sequencetools.AideSequence):
    """Water transfer that affects the water balance of the main model [m³/s].

    Positive values indicate withdrawals; negative values indicate supplies.
    """

    NDIM: Final[Literal[0]] = 0
