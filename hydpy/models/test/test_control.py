# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools


class K(parametertools.SingleParameter):
    """Storage coefficient [1/T].

    For educational purposes, the actual value of parameter :class:`K` does
    not depend on the difference between the actual simulation time step and
    the actual parameter time step.
    """
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of the Test model, directly defined by the user."""
    _PARCLASSES = (K,)
