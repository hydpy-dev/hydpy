# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.sw1d import sw1d_control


class Seconds(parametertools.SecondsParameter):
    """The length of the actual simulation step size in seconds [s]."""


class TOY(parametertools.TOYParameter):
    """References the |Indexer.timeofyear| index array provided by the instance of
    class |Indexer| available in module |pub| [-]."""


class WeightUpstream(parametertools.Parameter):
    """A weighting coefficient for interpolating the water level from the centroids of
    two adjacent segments to their shared edge [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (sw1d_control.LengthUpstream, sw1d_control.LengthDownstream)

    def update(self) -> None:
        r"""Update the value according to :math:`WeightUpstream = LengthDownstream
        / (LengthUpstream + LengthDownstream)`.

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> lengthupstream(1.0)
        >>> lengthdownstream(3.0)
        >>> derived.weightupstream.update()
        >>> derived.weightupstream
        weightupstream(0.75)
        """
        con = self.subpars.pars.control
        self.value = con.lengthdownstream / (con.lengthupstream + con.lengthdownstream)


class LengthMin(parametertools.Parameter):
    """The minimum length of the segments upstream and downstream of the relevant
    routing model [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (sw1d_control.LengthUpstream, sw1d_control.LengthDownstream)

    def update(self) -> None:
        """Take the minimum of |LengthUpstream| and |LengthDownstream|.

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> lengthupstream(2.0)
        >>> lengthdownstream(4.0)
        >>> derived.lengthmin.update()
        >>> derived.lengthmin
        lengthmin(2.0)
        """
        con = self.subpars.pars.control
        self.value = min(con.lengthupstream, con.lengthdownstream)


class LengthMean(parametertools.Parameter):
    """The mean length of the segments upstream and downstream of the relevant routing
    model [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (sw1d_control.LengthUpstream, sw1d_control.LengthDownstream)

    def update(self) -> None:
        """Take the mean of |LengthUpstream| and |LengthDownstream|.

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> lengthupstream(2.0)
        >>> lengthdownstream(4.0)
        >>> derived.lengthmean.update()
        >>> derived.lengthmean
        lengthmean(3.0)
        """
        con = self.subpars.pars.control
        self.value = (con.lengthupstream + con.lengthdownstream) / 2
