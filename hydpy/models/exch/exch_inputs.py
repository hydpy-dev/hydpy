# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class RequestedTransfer(sequencetools.InputSequence):
    """Externally requested water transfer [m³/s].

    Positive values are withdrawals, and negative values are supplies.  |numpy.nan| or
    |numpy.inf| (positive or negative) means that no external request is available.
    """

    NDIM: Final[Literal[0]] = 0
