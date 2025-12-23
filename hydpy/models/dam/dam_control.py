# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import timetools
from hydpy.auxs import interptools


class SurfaceArea(parametertools.Parameter):
    """Average size of the water surface [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CatchmentArea(parametertools.Parameter):
    """Size of the catchment draining into the dam [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class NmbLogEntries(parametertools.Parameter):
    """Number of log entries for certain variables [-].

    Note that setting a new value by calling the parameter object sets the shapes of
    all associated log sequences automatically, except those with a predefined default
    shape:

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
    loggedouterwaterlevel(nan)
    loggedremotewaterlevel(nan)

    To prevent losing information, updating parameter |NmbLogEntries| resets the shape
    of the relevant log sequences only when necessary:

    >>> logs.loggedtotalremotedischarge = 1.0
    >>> nmblogentries(3)
    >>> logs.loggedtotalremotedischarge
    loggedtotalremotedischarge(1.0, 1.0, 1.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        new_shape = (self.value,)
        for seq in self.subpars.pars.model.sequences.logs:
            old_shape = exceptiontools.getattr_(seq, "shape", (None,))
            if new_shape != old_shape:
                try:
                    seq.shape = new_shape
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

    def __call__(self, *args, **kwargs) -> None:
        self.shape = (-1,)
        parametertools.SeasonalParameter.__call__(self, *args, **kwargs)


class RemoteDischargeSafety(parametertools.SeasonalParameter):
    """Safety factor for reducing the risk of insufficient water release [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class WaterLevel2PossibleRemoteRelief(interptools.SimpleInterpolator):
    """An interpolation function describing the relationship between water level and
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


class MinimumRelease(parametertools.Parameter):
    """Minimum water release [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


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

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class WaterLevelMaximumThreshold(parametertools.Parameter):
    """The water level not to be exceeded [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class WaterLevelMaximumTolerance(parametertools.Parameter):
    """A tolerance value for the water level maximum [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class RemoteWaterLevelMaximumThreshold(parametertools.Parameter):
    """The remote water level not to be exceeded [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class RemoteWaterLevelMaximumTolerance(parametertools.Parameter):
    """Tolerance value for the remote water level maximum [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class ThresholdEvaporation(parametertools.Parameter):
    """The water level at which actual evaporation is 50 % of potential evaporation
    [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


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


class WaterVolume2WaterLevel(interptools.SimpleInterpolator):
    """An interpolation function that describes the relationship between water level
    and water volume [-]."""

    XLABEL = "water volume [million m³]"
    YLABEL = "water level [m]"


class WaterLevel2FloodDischarge(interptools.SeasonalInterpolator):
    """An interpolation function that describesg the relationship between flood
    discharge and water volume [-]."""

    XLABEL = "water level [m]"
    YLABEL = "flood discharge [m³/s]"


class WaterLevelDifference2MaxForcedDischarge(interptools.SeasonalInterpolator):
    """An interpolation function that describes the relationship between the highest
    possible forced discharge and the water level difference [-]."""

    XLABEL = "water level difference [m]"
    YLABEL = "max. forced discharge [m³/s]"


class WaterLevelDifference2MaxFreeDischarge(interptools.SeasonalInterpolator):
    """An interpolation function that describes the relationship between the highest
    possible free discharge and the water level difference [-]."""

    XLABEL = "water level difference [m]"
    YLABEL = "max. free discharge [m³/s]"


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


class MaximumVolume(parametertools.Parameter):
    """Maximum storable volume of water where uncontrolled discharge can be prevented
    [Mio. m³]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class VolumeTolerance(parametertools.Parameter):
    """Smoothing parameter for volume-related smoothing operations [Mio. m³]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class DischargeTolerance(parametertools.Parameter):
    """Smoothing parameter for discharge-related smoothing operations [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestLevel(parametertools.Parameter):
    """The crest level of a weir [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class CrestLevelTolerance(parametertools.Parameter):
    """A tolerance value for the crest level of a weir [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class NmbSafeReleaseModels(parametertools.Parameter):
    """The number of submodels that suggest release values that serve for flood
    protection at remote locations [-].

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> nmbsafereleasemodels(2)
    >>> model.safereleasemodels.number
    2
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.safereleasemodels.number = self.value


class Commission(parametertools.Parameter):
    """Commission date [-].

    Parameter |Commission|  requires a date as input.  It compares this date with the
    current initialisation period, which must therefore be defined first:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> commission("2000-01-05")
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: While trying to set the commission \
date via parameter `commission` of element `?`, the following error occurred: \
Attribute timegrids of module `pub` is not defined at the moment.

    After defining the initialisation period, you can pass the commission data, for
    example, in the form of a |Date| instance or a suitable string:

    >>> from hydpy import Date, pub
    >>> pub.timegrids = "2000-01-01", "2000-01-10", "1d"

    >>> commission(Date("2000-01-01"))
    >>> commission
    commission("2000-01-01 00:00:00")

    >>> commission("2000-01-05")
    >>> commission
    commission("2000-01-05 00:00:00")

    Parameter |Commission| internally transforms the given date into an index value with
    respect to the initialisation period:

    >>> commission.value
    4

    Commission dates outside the initialisation period pose no problems:

    >>> commission("1999-12-01")
    >>> commission
    commission("1999-12-01 00:00:00")
    >>> commission.value
    -31

    >>> commission("2000-02-01")
    >>> commission
    commission("2000-02-01 00:00:00")
    >>> commission.value
    31

    However, we expect a date that lies precisely at the start or end of one simulation
    step:

    >>> commission("2000-02-01 12:00")
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the commission date via parameter `commission` of \
element `?`, the following error occurred: The given date `2000-02-01 12:00:00` is not \
properly alligned on the indexed timegrid `Timegrid("2000-01-01 00:00:00", \
"2000-01-10 00:00:00", "1d")`.

    Alternatively, you can set the commission date by passing the mentioned index value:

    >>> commission(4)
    >>> commission
    commission("2000-01-05 00:00:00")
    >>> commission.value
    4
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)
    INIT = 0

    def __call__(self, *args, **kwargs) -> None:
        try:
            try:
                super().__call__(*args, **kwargs)
            except TypeError:
                self.value = hydpy.pub.timegrids.init[args[0]]
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to set the commission date via parameter "
                f"{objecttools.elementphrase(self)}"
            )

    def update(self) -> None:
        """Always fall back to the default value if the user provides none
        (deprecated).

        >>> import warnings
        >>> warnings.filterwarnings("error")

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> commission.update()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.HydPyDeprecationWarning: The value of parameter \
`commission` (introduced in HydPy 6.2), has not been explicitly defined and is \
automatically set to `1500-01-01 00:00:00`.  We will remove this fallback mechanism in \
HydPy 8.0; therefore, please consider updating your model setup.

        >>> commission
        commission("1500-01-01 00:00:00")

        >>> commission("2000-01-02")
        >>> commission
        commission("2000-01-02 00:00:00")
        >>> commission.value
        1
        """
        tg = hydpy.pub.timegrids.init
        date = tg[int((timetools.Date("1500-01-01") - tg.firstdate) / tg.stepsize)]
        self._update_newbie(value=date, version="6.2")

    def __repr__(self) -> str:
        return f'{self.name}("{hydpy.pub.timegrids.init[self.value]}")'
