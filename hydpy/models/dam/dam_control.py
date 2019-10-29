# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import anntools


class CatchmentArea(parametertools.Parameter):
    """Size of the catchment draining into the dam [km2]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


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
    loggedrequiredremoterelease(nan)
    loggedallowedremoterelieve(nan)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        for seq in self.subpars.pars.model.sequences.logs:
            try:
                seq.shape = self
            except AttributeError:
                pass


class RemoteDischargeMinimum(parametertools.SeasonalParameter):
    """Discharge threshold of a cross section far downstream that
    should not be undercut by the actual discharge [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def __call__(self, *args, **kwargs):
        self.shape = (None, )
        parametertools.SeasonalParameter.__call__(self, *args, **kwargs)


class RemoteDischargeSafety(parametertools.SeasonalParameter):
    """Safety factor to reduce the risk to release not enough water [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class WaterLevel2PossibleRemoteRelieve(anntools.ANN):
    """Artificial neural network describing the relationship between
    water level and the highest possible water release used to relieve
    the dam during high flow conditions [-]."""


class RemoteRelieveTolerance(parametertools.Parameter):
    """A tolerance value for the "possible remote relieve" [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class NearDischargeMinimumThreshold(parametertools.SeasonalParameter):
    """Discharge threshold of a cross section in the near of the dam that
    not be undercut by the actual discharge [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def __call__(self, *args, **kwargs):
        self.shape = (None, )
        parametertools.SeasonalParameter.__call__(self, *args, **kwargs)


class NearDischargeMinimumTolerance(parametertools.SeasonalParameter):
    """A tolerance value for the "near discharge minimum" [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class RestrictTargetedRelease(parametertools.Parameter):
    """A flag indicating whether low flow variability has to be preserved
    or not [-]."""
    NDIM, TYPE, TIME, SPAN = 0, bool, None, (None, None)


class WaterLevelMinimumThreshold(parametertools.Parameter):
    """The minimum operating water level of the dam [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumTolerance(parametertools.Parameter):
    """A tolarance value for the minimum operating water level [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumRemoteThreshold(parametertools.Parameter):
    """The minimum operating water level of the dam regarding remote
    water supply [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumRemoteTolerance(parametertools.Parameter):
    """A tolarance value for the minimum operating water level regarding
    remote water supply [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class HighestRemoteRelieve(parametertools.SeasonalParameter):
    """The highest possible relieve discharge from another location [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelRelieveThreshold(parametertools.SeasonalParameter):
    """The threshold water level of the dam regarding the allowed
    relieve discharge from another location [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelRelieveTolerance(parametertools.SeasonalParameter):
    """A tolerance value for parameter |WaterLevelRelieveThreshold| [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class HighestRemoteSupply(parametertools.SeasonalParameter):
    """The highest possible supply discharge from another location [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelSupplyThreshold(parametertools.SeasonalParameter):
    """The threshold water level of the dam regarding the requried
    supply discharge from another location [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class WaterLevelSupplyTolerance(parametertools.SeasonalParameter):
    """A tolerance value for parameter |WaterLevelSupplyThreshold| [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class HighestRemoteDischarge(parametertools.Parameter):
    """The highest possible discharge between two remote locations [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class HighestRemoteTolerance(parametertools.Parameter):
    """Smoothing parameter associated with |HighestRemoteDischarge| [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class WaterVolume2WaterLevel(anntools.ANN):
    """Artificial neural network describing the relationship between
    water level and water volume [-]."""


class WaterLevel2FloodDischarge(anntools.SeasonalANN):
    """Artificial neural network describing the relationship between
    flood discharge and water volume [-]."""
