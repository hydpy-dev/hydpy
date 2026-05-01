# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools


class LoggedWaterLevel(sequencetools.LogSequenceFixed):
    """Logged water level [m]."""

    SHAPE = 1


class LoggedWaterLevels(sequencetools.LogSequenceFixed):
    """Logged water levels [m]."""

    SHAPE = 2
