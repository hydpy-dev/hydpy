# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
from hydpy.auxs import anntools


class CatchmentArea(parametertools.SingleParameter):
    """Size of the catchment draining into the dam [km2]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class NmbLogEntries(parametertools.SingleParameter):
    """Number of log entries for certain variables [m3/s].

    Note that setting a new value by calling the parameter object sets
    the shapes of all associated log sequences automatically, except those
    with a predefined default shape:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> nmblogentries(3)
    >>> for (name, seq) in logs:
    ...     print(seq)
    loggedtotalremotedischarge(nan, nan, nan)
    loggedoutflow(nan, nan, nan)
    loggedrequiredremoterelease(nan, nan)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super(NmbLogEntries, self).__call__(*args, **kwargs)
        for (dummy, seq) in self.subpars.pars.model.sequences.logs:
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
        super(RemoteDischargeMinimum, self).__call__(*args, **kwargs)


class RemoteDischargeSavety(parametertools.SeasonalParameter):
    """Safety factor to reduce the risk to release not enough water [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def __call__(self, *args, **kwargs):
        self.shape = (None, )
        super(RemoteDischargeSavety, self).__call__(*args, **kwargs)


class NearDischargeMinimumThreshold(parametertools.SeasonalParameter):
    """Discharge threshold of a cross section in the near of the dam that
    not be undercut by the actual discharge [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def __call__(self, *args, **kwargs):
        self.shape = (None, )
        super(NearDischargeMinimumThreshold, self).__call__(*args, **kwargs)


class NearDischargeMinimumTolerance(parametertools.SeasonalParameter):
    """A tolerance value for the "near discharge minimum" [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def __call__(self, *args, **kwargs):
        self.shape = (None, )
        super(NearDischargeMinimumTolerance, self).__call__(*args, **kwargs)


class WaterLevelMinimumThreshold(parametertools.SingleParameter):
    """The minimum operating water level of the dam [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumTolerance(parametertools.SingleParameter):
    """A tolarance value for the minimum operating water level [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumRemoteThreshold(parametertools.SingleParameter):
    """The minimum operating water level of the dam regarding remote
    water supply [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterLevelMinimumRemoteTolerance(parametertools.SingleParameter):
    """A tolarance value for the minimum operating water level regarding
    remote water supply[m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class WaterVolume2WaterLevel(anntools.ANN):
    """Artificial neural network describing the relationship between
    water level and water volume [-]."""


class WaterLevel2FloodDischarge(anntools.ANN):
    """Artificial neural network describing the relationship between
    flood discharge and water volume [-]."""


class ControlParameters(parametertools.SubParameters):
    """Control parameters of the dam model, directly defined by the user."""
    _PARCLASSES = (CatchmentArea,
                   NmbLogEntries,
                   RemoteDischargeMinimum,
                   RemoteDischargeSavety,
                   NearDischargeMinimumThreshold,
                   NearDischargeMinimumTolerance,
                   WaterLevelMinimumRemoteThreshold,
                   WaterLevelMinimumRemoteTolerance,
                   WaterLevelMinimumThreshold,
                   WaterLevelMinimumTolerance,
                   WaterVolume2WaterLevel,
                   WaterLevel2FloodDischarge)
