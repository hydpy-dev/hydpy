# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools


class Lag(parametertools.SingleParameter):
    """Time lag between inflow and outflow [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)


class Damp(parametertools.SingleParameter):
    """Damping of the hydrograph [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of hstream, directly defined by the user."""
    CLASSES = (Lag,
               Damp)
