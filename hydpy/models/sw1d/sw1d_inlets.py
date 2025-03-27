# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LongQ(sequencetools.InletSequence):
    """The longitudinal inflow into the first channel segment [m³/s]."""

    NDIM, NUMERIC = 1, False


class LatQ(sequencetools.InletSequence):
    """The lateral inflow into the first channel segment [m³/s]."""

    NDIM, NUMERIC = 1, False


class WaterLevel(sequencetools.InletSequence):
    """Water level [m]."""

    NDIM, NUMERIC = 0, False
