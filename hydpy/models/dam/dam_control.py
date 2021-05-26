# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import anntools


class SurfaceArea(parametertools.Parameter):
    """Average size of the water surface [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CatchmentArea(parametertools.Parameter):
    """Size of the catchment draining into the dam [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class NmbLogEntries(parametertools.Parameter):
    """Number of log entries for certain variables [-].

    Note that setting a new value by calling the parameter object sets
    the shapes of all associated log sequences automatically, except those
    with a predefined default shape:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> nmblogentries(3)
    >>> for seq in logs:
    ...     print(seq)
    loggedtotalremotedischarge(nan, nan, nan)
    loggedoutflow(nan, nan, nan)
    loggedadjustedevaporation(nan)
    loggedrequiredremoterelease(nan)
    loggedallowedremoterelief(nan)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        for seq in self.subpars.pars.model.sequences.logs:
            try:
                seq.shape = self
            except AttributeError:
                pass


class CorrectionPrecipitation(parametertools.Parameter):
    """Precipitation correction factor [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CorrectionEvaporation(parametertools.Parameter):
    """Evaporation correction factor [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class WeightEvaporation(parametertools.Parameter):
    """Time weighting factor for evaporation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, 1.0)


class RemoteDischargeMinimum(parametertools.SeasonalParameter):
    """Discharge threshold of a cross-section far downstream not to be undercut by the
    actual discharge [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    def __call__(self, *args, **kwargs):
        self.shape = (None,)
        parametertools.SeasonalParameter.__call__(self, *args, **kwargs)


class RemoteDischargeSafety(parametertools.SeasonalParameter):
    """Safety factor for reducing the risk to release not enough water [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class WaterLevel2PossibleRemoteRelief(anntools.ANN):
    """Artificial neural network describing the relationship between water level and
    the highest possible water release used to relieve the dam during high flow
    conditions [-]."""

    XLABEL = "water level [m]"
    YLABEL = "possible remote relieve [m³/s]"


class RemoteReliefTolerance(parametertools.Parameter):
    """A tolerance value for |PossibleRemoteRelief| [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class NearDischargeMinimumThreshold(parametertools.SeasonalParameter):
    """Discharge threshold of a cross-section near the dam not to be undercut by the
    actual discharge [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class NearDischargeMinimumTolerance(parametertools.SeasonalParameter):
    """A tolerance value for the "near discharge minimum" [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class RestrictTargetedRelease(parametertools.Parameter):
    """A flag indicating whether low flow variability has to be preserved
    or not [-]."""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (None, None)


class WaterVolumeMinimumThreshold(parametertools.SeasonalParameter):
    """The minimum operating water volume of the dam [million m³]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)


class WaterLevelMinimumThreshold(parametertools.Parameter):
    """The minimum operating water level of the dam [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class WaterLevelMinimumTolerance(parametertools.Parameter):
    """A tolerance value for the minimum operating water level [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class ThresholdEvaporation(parametertools.Parameter):
    """The water level at which actual evaporation is 50 % of potential evaporation
    [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class ToleranceEvaporation(parametertools.Parameter):
    """A tolerance value defining the steepness of the transition of actual evaporation
    between zero and potential evaporation [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumRemoteThreshold(parametertools.Parameter):
    """The minimum operating water level of the dam regarding remote water supply
    [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumRemoteTolerance(parametertools.Parameter):
    """A tolerance value for the minimum operating water level regarding remote water
    supply [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class HighestRemoteRelief(parametertools.SeasonalParameter):
    """The highest possible relief discharge from another location [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelReliefThreshold(parametertools.SeasonalParameter):
    """The threshold water level of the dam regarding the allowed relief discharge from
    another location [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelReliefTolerance(parametertools.SeasonalParameter):
    """A tolerance value for parameter |WaterLevelReliefThreshold| [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class HighestRemoteSupply(parametertools.SeasonalParameter):
    """The highest possible supply discharge from another location [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelSupplyThreshold(parametertools.SeasonalParameter):
    """The threshold water level of the dam regarding the required supply discharge
    from another location [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelSupplyTolerance(parametertools.SeasonalParameter):
    """A tolerance value for parameter |WaterLevelSupplyThreshold| [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class HighestRemoteDischarge(parametertools.Parameter):
    """The highest possible discharge between two remote locations [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class HighestRemoteTolerance(parametertools.Parameter):
    """Smoothing parameter associated with |HighestRemoteDischarge| [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class WaterVolume2WaterLevel(anntools.ANN):
    """Artificial neural network describing the relationship between water level and
    water volume [-]."""

    XLABEL = "water volume [million m³]"
    YLABEL = "water level [m]"


class WaterLevel2FloodDischarge(anntools.SeasonalANN):
    """Artificial neural network describing the relationship between flood discharge
    and water volume [-]."""

    XLABEL = "water level [m]"
    YLABEL = "flood discharge [m³/s]"


class AllowedWaterLevelDrop(parametertools.Parameter):
    """The highest allowed water level decrease [m/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)


class AllowedDischargeTolerance(parametertools.Parameter):
    """Smoothing parameter eventually associated with |AllowedWaterLevelDrop| [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class AllowedRelease(parametertools.SeasonalParameter):
    """The maximum water release not causing any harm downstream [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class TargetVolume(parametertools.SeasonalParameter):
    """The desired volume of water required within the dam at specific times of the
    year [Mio. m³]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class TargetRangeAbsolute(parametertools.Parameter):
    """The absolute interpolation range related to parameter |TargetVolume|
    [Mio. m³]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class TargetRangeRelative(parametertools.Parameter):
    """The relative interpolation range related to parameter |TargetVolume| [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class VolumeTolerance(parametertools.Parameter):
    """Smoothing parameter for volume related smoothing operations [Mio. m³]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class DischargeTolerance(parametertools.Parameter):
    """Smoothing parameter for discharge related smoothing operations [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
