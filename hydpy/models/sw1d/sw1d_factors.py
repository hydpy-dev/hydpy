# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.sw1d import sw1d_control


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
    """The water level within all segments of a channel [m].

    Parameter |NmbSegments| determines the length of |WaterLevels|:

    >>> from hydpy.models.sw1d_channel import *
    >>> parameterstep()
    >>> nmbsegments(2)
    >>> factors.waterlevels.shape
    (2,)

    |NmbSegments| preserves existing values if the number of segments does not change:

    >>> factors.waterlevels = 1.0, 2.0
    >>> nmbsegments(2)
    >>> factors.waterlevels
    waterlevels(1.0, 2.0)

    Changing the number of segments resets the values:

    >>> nmbsegments(1)
    >>> factors.waterlevels
    waterlevels(nan)
    """

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, sw1d_control.NmbSegments):
            self.__hydpy__change_shape_if_necessary__((p.value,))


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
