# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class MaxTimeStep(sequencetools.FactorSequence):
    """The highest possible computation time step according to local stability
    considerations [s]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class TimeStep(sequencetools.FactorSequence):
    """The actual computation step according to global stability considerations [s]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class WaterDepth(sequencetools.FactorSequence):
    """Water depth [m].

    Difference between the elevations of the water surface and the channel bottom.
    """

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class WaterLevel(sequencetools.FactorSequence):
    """Water level [m].

    The sum of the channel's bottom elevation and water depth.
    """

    NDIM, NUMERIC = 0, False


class WaterLevels(sequencetools.FactorSequence):
    """The water level within all segments of a channel [m]."""

    NDIM, NUMERIC = 1, False


class WaterLevelUpstream(sequencetools.FactorSequence):
    """The upstream channel segment's water level [m]."""

    NDIM, NUMERIC = 0, False


class WaterLevelDownstream(sequencetools.FactorSequence):
    """The downstream channel segment's water level [m]."""

    NDIM, NUMERIC = 0, False


class WaterVolumeUpstream(sequencetools.FactorSequence):
    """The upstream channel segment's water volume [1000 m³]."""

    NDIM, NUMERIC = 0, False


class WaterVolumeDownstream(sequencetools.FactorSequence):
    """The downstream channel segment's water volume [1000 m³]."""

    NDIM, NUMERIC = 0, False


class WettedArea(sequencetools.FactorSequence):
    """The channel wetted area [m²]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class WettedPerimeter(sequencetools.FactorSequence):
    """The channel wetted perimeter [m]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)
