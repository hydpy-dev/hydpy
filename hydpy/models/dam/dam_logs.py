# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LoggedTotalRemoteDischarge(sequencetools.LogSequence):
    """Logged discharge values from somewhere else [m³/s]."""

    NDIM: Final[Literal[1]] = 1


class LoggedOutflow(sequencetools.LogSequence):
    """Logged discharge values from the dam itself [m³/s]."""

    NDIM: Final[Literal[1]] = 1


class LoggedAdjustedEvaporation(sequencetools.LogSequenceFixed):
    """Logged adjusted evaporation [m³/s]."""

    SHAPE = 1


class LoggedRequiredRemoteRelease(sequencetools.LogSequenceFixed):
    """Logged required discharge values computed by another model [m³/s]."""

    SHAPE = 1


class LoggedAllowedRemoteRelief(sequencetools.LogSequenceFixed):
    """Logged allowed discharge values computed by another model [m³/s]."""

    SHAPE = 1


class LoggedOuterWaterLevel(sequencetools.LogSequenceFixed):
    """Logged water level directly below the dam [m]."""

    SHAPE = 1


class LoggedRemoteWaterLevel(sequencetools.LogSequenceFixed):
    """Logged water level at a remote location [m]."""

    SHAPE = 1
