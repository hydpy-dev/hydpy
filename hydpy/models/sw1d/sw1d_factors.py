# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class MaxTimeStep(sequencetools.FactorSequence):
    """The highest possible computation time step according to local stability
    considerations [s]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)


class TimeStep(sequencetools.FactorSequence):
    """The actual computation step according to global stability considerations [s]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)


class WaterDepth(sequencetools.FactorSequence):
    """Water depth [m].

    Difference between the elevations of the water surface and the channel bottom.
    """

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)


class WaterLevel(sequencetools.FactorSequence):
    """Water level [m].

    The sum of the channel's bottom elevation and water depth.
    """

    NDIM: Final[Literal[0]] = 0


class WaterLevels(sequencetools.FactorSequence):
    """The water level within all segments of a channel [m]."""

    NDIM: Final[Literal[1]] = 1


class WaterLevelUpstream(sequencetools.FactorSequence):
    """The upstream channel segment's water level [m]."""

    NDIM: Final[Literal[0]] = 0


class WaterLevelDownstream(sequencetools.FactorSequence):
    """The downstream channel segment's water level [m]."""

    NDIM: Final[Literal[0]] = 0


class WaterVolumeUpstream(sequencetools.FactorSequence):
    """The upstream channel segment's water volume [1000 m³]."""

    NDIM: Final[Literal[0]] = 0


class WaterVolumeDownstream(sequencetools.FactorSequence):
    """The downstream channel segment's water volume [1000 m³]."""

    NDIM: Final[Literal[0]] = 0


class WettedArea(sequencetools.FactorSequence):
    """The channel wetted area [m²]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)


class WettedPerimeter(sequencetools.FactorSequence):
    """The channel wetted perimeter [m]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)
