# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *

# ...from sw1d
from hydpy.models.sw1d import sw1d_fluxes


class NmbSegments(parametertools.Parameter):
    """The number of channel segments [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        model = self.subpars.pars.model
        model.storagemodels.number = self.value
        model.routingmodels.number = self.value + 1
        for subseqs in self.subpars.pars.model.sequences:
            for seq in (s for s in subseqs if s.NDIM == 1):
                seq._set_shape(self.value + isinstance(seq, sw1d_fluxes.Discharges))


class Length(parametertools.Parameter):
    """The length of a single channel segment [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class LengthUpstream(parametertools.Parameter):
    """The upstream channel segment's length [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class LengthDownstream(parametertools.Parameter):
    """The downstream channel segment's length [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BottomLevel(parametertools.Parameter):
    """The channel bottom elevation [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class BottomWidth(parametertools.Parameter):
    """The channel bottom width [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class SideSlope(parametertools.Parameter):
    """The channel side slope [-].

    A value of zero corresponds to a rectangular channel shape.  A value of two
    corresponds to an increase of half a meter in elevation for each additional meter
    distance from the channel bottom.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class StricklerCoefficient(parametertools.Parameter):
    """The average Gauckler-Manning-Strickler coefficient [m^(1/3)/s].

    The higher the coefficient's value, the higher the calculated discharge.  Typical
    values range from 20 to 80.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class TimeStepFactor(parametertools.Parameter):
    """A factor for reducing the estimated computation time step to increase numerical
    stability [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)


class DiffusionFactor(parametertools.Parameter):
    """A factor for introducing numerical diffusion to increase numerical stability
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)


class CrestHeight(parametertools.Parameter):
    """The weir crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class CrestWidth(parametertools.Parameter):
    """The weir crest width [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class FlowCoefficient(parametertools.Parameter):
    """The weir flow coefficient [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.62
