# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools


class NmbSegments(parametertools.SingleParameter):
    """Number of river segments [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)


class C1(parametertools.SingleParameter):
    """First coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., .5)


class C2(parametertools.SingleParameter):
    """Second coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)


class C3(parametertools.SingleParameter):
    """Third coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., .5)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of hstream, indirectly defined by the user."""
    _PARCLASSES = (NmbSegments, C1, C2, C3)
