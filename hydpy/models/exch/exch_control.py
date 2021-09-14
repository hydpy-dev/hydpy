# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class CrestHeight(parametertools.Parameter):
    """Crest height [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CrestWidth(parametertools.Parameter):
    """Crest width [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class FlowCoefficient(parametertools.Parameter):
    """Flow coefficient [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.62


class FlowExponent(parametertools.Parameter):
    """Flow exponent [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5


class AllowedExchange(parametertools.Parameter):
    """The highest water exchange allowed [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5
