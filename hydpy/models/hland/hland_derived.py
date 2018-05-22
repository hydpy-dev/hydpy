# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.hland import hland_parameters


class RelZoneArea(hland_parameters.MultiParameter):
    """Relative zone area [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)


class RelSoilArea(parametertools.SingleParameter):
    """Total area of all `field` and `forest` zones [km²]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)


class RelSoilZoneArea(hland_parameters.MultiParameter):
    """Relative zone area of all `field` and `forest` zones [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)


class RelLandZoneArea(hland_parameters.MultiParameter):
    """Relative Zone area of all `field`, `forest` and `glacier` zones [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)


class RelLandArea(parametertools.SingleParameter):
    """Quotient of the sum of |LandZoneArea| and |Area| [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)


class TTM(hland_parameters.MultiParameterLand):
    """Threshold temperature for snow melting and refreezing [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class DT(parametertools.SingleParameter):
    """Relative time step length for the upper zone layer calculations [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)


class NmbUH(parametertools.SingleParameter):
    """Number of the required unit hydrograph ordinates [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)


class UH(parametertools.MultiParameter):
    """Unit hydrograph ordinates [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)


class QFactor(parametertools.SingleParameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-H-Land, indirectly defined by the user."""
    _PARCLASSES = (RelZoneArea, RelSoilArea, RelSoilZoneArea, RelLandZoneArea,
                   RelLandArea, TTM, DT, NmbUH, UH, QFactor)
