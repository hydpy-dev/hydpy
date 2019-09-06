# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class K(parametertools.Parameter):
    """Storage coefficient [1/T].

    For educational purposes, the actual value of parameter |K| does
    not depend on the difference between the actual simulation time step and
    the actual parameter time step.
    """
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of the Test model, directly defined by the user."""
    CLASSES = (K,)
