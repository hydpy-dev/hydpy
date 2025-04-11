# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedWaterLevel(sequencetools.LogSequenceFixed):
    """Logged water level [m]."""

    NUMERIC = False
    SHAPE = 1


class LoggedWaterLevels(sequencetools.LogSequenceFixed):
    """Logged water levels [m]."""

    NUMERIC = False
    SHAPE = 2
