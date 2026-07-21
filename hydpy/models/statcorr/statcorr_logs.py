from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LoggedObservedDischarge(sequencetools.LogSequence):
    """Logged observed discharge [m³/s]"""

    NDIM: Final[Literal[1]] = 1


class LoggedSimulatedDischarge(sequencetools.LogSequence):
    """Logged simulated discharge [m³/s]."""

    NDIM: Final[Literal[1]] = 1
