# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.auxs import interptools

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


class DampingRadius(parametertools.Parameter):
    """The radius of flow rate reductions around neuralgic water levels to prevent
    oscillations due to numerical inaccuracies [m].

    For a value of zero, the radius of action is zero, with no modification of the
    target equation and, thus, no artificial damping.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestHeight(parametertools.Parameter):
    """The weir crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class CrestWidth(parametertools.Parameter):
    """The weir crest width [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class GateHeight(parametertools.CallbackParameter):
    """The gate lower edge's height [m].

    Parameter |GateHeight| offers the possibility of assigning a callback function for
    calculating variable gate heights instead of setting a fixed one.  See the
    |Calc_Discharge_V3| documentation for further information.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class GateWidth(parametertools.Parameter):
    """The gate width [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class FlowCoefficient(parametertools.Parameter):
    """The weir flow coefficient [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.62


class TargetWaterLevel1(parametertools.Parameter):
    """The lower target water level [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim |TargetWaterLevel1| following
        :math:`TargetWaterLevel1 \leq TargetWaterLevel2`.

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> targetwaterlevel2(2.0)
        >>> targetwaterlevel1(3.0)
        >>> targetwaterlevel1
        targetwaterlevel1(2.0)
        """
        if upper is None:
            upper = exceptiontools.getattr_(
                self.subpars.targetwaterlevel2, "value", None
            )
        return super().trim(lower, upper)


class TargetWaterLevel2(parametertools.Parameter):
    """The upper target water level [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim |TargetWaterLevel2| following
        :math:`TargetWaterLevel1 \leq TargetWaterLevel2`.

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> targetwaterlevel1(2.0)
        >>> targetwaterlevel2(1.0)
        >>> targetwaterlevel2
        targetwaterlevel2(2.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(
                self.subpars.targetwaterlevel1, "value", None
            )
        return super().trim(lower, upper)


class BottomLowWaterThreshold(parametertools.SeasonalParameter):
    """Water level below which gates are fully closed to stop drainage during low flow
    periods [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class UpperLowWaterThreshold(parametertools.SeasonalParameter):
    """Water level below which gates are partly closed to reduce drainage during low
    flow periods [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class BottomHighWaterThreshold(parametertools.SeasonalParameter):
    """Water level above which gate operation is partly sluice-like to increase
    drainage during high flow periods [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class UpperHighWaterThreshold(parametertools.SeasonalParameter):
    """Water level above which gate operation is fully sluice-like to maximise drainage
    during high flow periods [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class Gradient2PumpingRate(interptools.SimpleInterpolator):
    """An interpolation function describing the relationship between the water
    level height to be overcome and the maximum possible pumping rate [-]."""

    XLABEL = "water level gradient [m]"
    YLABEL = "maximum pumping rate [m³/s]"
