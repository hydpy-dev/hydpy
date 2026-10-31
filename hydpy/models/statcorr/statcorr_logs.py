# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LoggedObservedValue(sequencetools.LogSequence):
    """Logged observed values [unit of the corrected variable]"""

    NDIM: Final[Literal[1]] = 1


class LoggedSimulatedValue(sequencetools.LogSequence):
    """Logged simulated values [unit of the corrected variable]."""

    NDIM: Final[Literal[1]] = 1
