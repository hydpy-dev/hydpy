# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LongQ(sequencetools.InletSequence):
    """The longitudinal inflow into the first channel segment [m³/s]."""

    NDIM = 1
    NUMERIC = False


class LatQ(sequencetools.InletSequence):
    """The lateral inflow into the first channel segment [m³/s]."""

    NDIM = 1
    NUMERIC = False


class WaterLevel(sequencetools.InletSequence):
    """Water level [m]."""

    NDIM = 0
    NUMERIC = False
