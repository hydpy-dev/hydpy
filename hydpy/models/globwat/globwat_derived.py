# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.globwat import globwat_parameters

SAFETY = 1e-14

class Irrigation(parametertools.MultiParameter):
    """landuse equipped for irrigation (True or False)."""
    NDIM, TYPE, TIME, SPAN = 1, bool, None, (None, None)

class SMax(parametertools.MultiParameter):
    """maximum soil moisture storage [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

class SEAv(parametertools.MultiParameter):
    """easily available soil moisture [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

class MOY(parametertools.IndexParameter):
    """References the "global" month of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, 11)

class RelArea(parametertools.MultiParameter):
    """relative area [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, 1)

class QFactor(parametertools.SingleParameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of globwat, indirectly defined by the user."""
    _PARCLASSES = (Irrigation, SMax, SEAv, MOY, RelArea, QFactor)
