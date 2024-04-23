# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# from site-packages

# ...from HydPy
from hydpy.core import parametertools

# ...from gland


class Area(parametertools.Parameter):
    """Subbasin area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class X1(parametertools.Parameter):
    """Maximum capacity of the production storage [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class X2(parametertools.Parameter):
    """Groundwater exchange coefficient (positive for water imports, negative for
    exports) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class X3(parametertools.Parameter):
    """One timestep ahead maximum capacity of the routing store [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class X4(parametertools.Parameter):
    """Time base of unit hydrographs |UH1| (|X4|) and |UH2| (2*|X4|) [T]."""

    # todo: obere Grenze unit hydrograph 20 Tage?

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.5, None)


class X5(parametertools.Parameter):
    """Intercatchment exchange threshold [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class X6(parametertools.Parameter):
    """coefficient for emptying exponential store [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)
