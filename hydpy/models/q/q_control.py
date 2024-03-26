# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring
# import...
# ...from HydPy
from hydpy.core import parametertools


class ChannelDepth(parametertools.Parameter):
    """Channel depth [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestHeight(parametertools.Parameter):
    """The height of the weir's crest above the channel bottom [m].

    Set |CrestHeight| to zero for channels without weirs.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestHeightTolerance(parametertools.Parameter):
    """Smoothing parameter related to the difference between the water depth and the
    crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BankfullDischarge(parametertools.Parameter):
    """Bankfull discharge [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)


class DischargeExponent(parametertools.Parameter):
    """Exponent of the water depth-discharge relation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5
