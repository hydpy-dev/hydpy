# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import variabletools
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

    def trim(self, lower=None, upper=None) -> bool:
        """Trim |BottomLowWaterThreshold| following
        :math:`BottomLowWaterThreshold \\leq UpperLowWaterThreshold` and
        :math:`BottomLowWaterThreshold \\leq BottomHighWaterThreshold` and
        :math:`BottomLowWaterThreshold \\leq UpperHighWaterThreshold`.

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2000-01-06", "1d"
        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> bottomlowwaterthreshold(2.0)
        >>> bottomlowwaterthreshold
        bottomlowwaterthreshold(2.0)

        >>> upperlowwaterthreshold.shape = 1
        >>> upperlowwaterthreshold.values[:5] = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> bottomhighwaterthreshold.shape = 1
        >>> bottomhighwaterthreshold.values[:5] = 5.0, 4.0, 3.0, 2.0, 1.0
        >>> upperhighwaterthreshold.shape = 1
        >>> upperhighwaterthreshold.values[:5] = 3.0, 2.0, 1.0, 2.0, 3.0
        >>> bottomlowwaterthreshold(2.0)
        >>> round_(bottomlowwaterthreshold.values[:5])
        1.0, 2.0, 1.0, 2.0, 1.0
        >>> from hydpy.core.testtools import warn_later
        >>> with pub.options.warntrim(True), warn_later():
        ...     bottomlowwaterthreshold
        bottomlowwaterthreshold(2.0)
        UserWarning: The "background values" of parameter `bottomlowwaterthreshold` \
of element `?` have been trimmed but not its original time of year-specific values.  \
Using the latter without modification might result in inconsistencies.
        """
        if upper is None:
            getattr_ = exceptiontools.getattr_
            upper = variabletools.combine_arrays_to_lower_or_upper_bound(
                getattr_(self.subpars.upperlowwaterthreshold, "values", None),
                getattr_(self.subpars.bottomhighwaterthreshold, "values", None),
                getattr_(self.subpars.upperhighwaterthreshold, "values", None),
                lower=False,
            )
        return super().trim(lower, upper)


class UpperLowWaterThreshold(parametertools.SeasonalParameter):
    """Water level below which gates are partly closed to reduce drainage during low
    flow periods [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
        """Trim |UpperLowWaterThreshold| following
        :math:`UpperLowWaterThreshold \\geq BottomLowWaterThreshold` and
        :math:`UpperLowWaterThreshold \\leq UpperHighWaterThreshold`.

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2000-01-06", "1d"
        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> upperlowwaterthreshold(4.0)
        >>> upperlowwaterthreshold
        upperlowwaterthreshold(4.0)

        >>> bottomlowwaterthreshold.shape = 1
        >>> bottomlowwaterthreshold.values[:5] = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> upperhighwaterthreshold.shape = 1
        >>> upperhighwaterthreshold.values[:5] = 3.0, 4.0, 5.0, 6.0, 7.0
        >>> upperlowwaterthreshold(4.0)
        >>> round_(upperlowwaterthreshold.values[:5])
        3.0, 4.0, 4.0, 4.0, 5.0
        >>> from hydpy.core.testtools import warn_later
        >>> with pub.options.warntrim(True), warn_later():
        ...     upperlowwaterthreshold
        upperlowwaterthreshold(4.0)
        UserWarning: The "background values" of parameter `upperlowwaterthreshold` of \
element `?` have been trimmed but not its original time of year-specific values.  \
Using the latter without modification might result in inconsistencies.
        """
        getattr_ = exceptiontools.getattr_
        if lower is None:
            lower = getattr_(self.subpars.bottomlowwaterthreshold, "values", None)
        if upper is None:
            upper = getattr_(self.subpars.upperhighwaterthreshold, "values", None)
        return super().trim(lower, upper)


class BottomHighWaterThreshold(parametertools.SeasonalParameter):
    """Water level above which gate operation is partly sluice-like to increase
    drainage during high flow periods [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
        """Trim |BottomHighWaterThreshold| following
        :math:`BottomHighWaterThreshold \\geq BottomLowWaterThreshold` and
        :math:`BottomHighWaterThreshold \\leq UpperHighWaterThreshold`.

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2000-01-06", "1d"
        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> bottomhighwaterthreshold(4.0)
        >>> bottomhighwaterthreshold
        bottomhighwaterthreshold(4.0)

        >>> bottomlowwaterthreshold.shape = 1
        >>> bottomlowwaterthreshold.values[:5] = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> upperhighwaterthreshold.shape = 1
        >>> upperhighwaterthreshold.values[:5] = 3.0, 4.0, 5.0, 6.0, 7.0
        >>> bottomhighwaterthreshold(4.0)
        >>> round_(bottomhighwaterthreshold.values[:5])
        3.0, 4.0, 4.0, 4.0, 5.0
        >>> from hydpy.core.testtools import warn_later
        >>> with pub.options.warntrim(True), warn_later():
        ...     bottomhighwaterthreshold
        bottomhighwaterthreshold(4.0)
        UserWarning: The "background values" of parameter `bottomhighwaterthreshold` \
of element `?` have been trimmed but not its original time of year-specific values.  \
Using the latter without modification might result in inconsistencies.
        """
        getattr_ = exceptiontools.getattr_
        if lower is None:
            lower = getattr_(self.subpars.bottomlowwaterthreshold, "values", None)
        if upper is None:
            upper = getattr_(self.subpars.upperhighwaterthreshold, "values", None)
        return super().trim(lower, upper)


class UpperHighWaterThreshold(parametertools.SeasonalParameter):
    """Water level above which gate operation is fully sluice-like to maximise drainage
    during high flow periods [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
        """Trim |UpperHighWaterThreshold| following
        :math:`UpperHighWaterThreshold \\geq BottomLowWaterThreshold` and
        :math:`UpperHighWaterThreshold \\geq UpperLowWaterThreshold` and
        :math:`UpperHighWaterThreshold \\geq BottomHighWaterThreshold`.

        >>> from hydpy import pub, round_
        >>> pub.timegrids = "2000-01-01", "2000-01-06", "1d"
        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> upperhighwaterthreshold(4.0)
        >>> upperhighwaterthreshold
        upperhighwaterthreshold(4.0)

        >>> bottomlowwaterthreshold.shape = 1
        >>> bottomlowwaterthreshold.values[:5] = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> upperlowwaterthreshold.shape = 1
        >>> upperlowwaterthreshold.values[:5] = 5.0, 4.0, 3.0, 2.0, 1.0
        >>> bottomhighwaterthreshold.shape = 1
        >>> bottomhighwaterthreshold.values[:5] = 3.0, 4.0, 5.0, 4.0, 3.0
        >>> upperhighwaterthreshold(4.0)
        >>> round_(upperhighwaterthreshold.values[:5])
        5.0, 4.0, 5.0, 4.0, 5.0
        >>> from hydpy.core.testtools import warn_later
        >>> with pub.options.warntrim(True), warn_later():
        ...     upperhighwaterthreshold
        upperhighwaterthreshold(4.0)
        UserWarning: The "background values" of parameter `upperhighwaterthreshold` \
of element `?` have been trimmed but not its original time of year-specific values.  \
Using the latter without modification might result in inconsistencies.
        """
        if lower is None:
            getattr_ = exceptiontools.getattr_
            lower = variabletools.combine_arrays_to_lower_or_upper_bound(
                getattr_(self.subpars.bottomlowwaterthreshold, "values", None),
                getattr_(self.subpars.upperlowwaterthreshold, "values", None),
                getattr_(self.subpars.bottomhighwaterthreshold, "values", None),
                lower=True,
            )
        return super().trim(lower, upper)


class Gradient2PumpingRate(interptools.SimpleInterpolator):
    """An interpolation function describing the relationship between the water
    level height to be overcome and the maximum possible pumping rate [-]."""

    XLABEL = "water level gradient [m]"
    YLABEL = "maximum pumping rate [m³/s]"
