# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *

from hydpy.models.musk import musk_control


class Seconds(parametertools.SecondsParameter):
    """Length of the actual simulation step size [s]."""


class SegmentLength(parametertools.Parameter):
    """The length of each channel segments [km]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    CONTROLPARAMETERS = (musk_control.Length,)

    def update(self) -> None:
        r"""Update the segment length based on
        :math:`SegmentLength = Length / NmbSegments`.

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> length(8.0)
        >>> derived.segmentlength.update()
        >>> derived.segmentlength
        segmentlength(4.0)
        """
        control = self.subpars.pars.control
        self.values = control.length.value / control.nmbsegments.value
