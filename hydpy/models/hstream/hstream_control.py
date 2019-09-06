# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class Lag(parametertools.Parameter):
    """Time lag between inflow and outflow [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)


class Damp(parametertools.Parameter):
    """Damping of the hydrograph [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of hstream, directly defined by the user."""
    CLASSES = (Lag,
               Damp)
