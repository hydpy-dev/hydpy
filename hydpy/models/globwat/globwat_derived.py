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

class SMax(parametertools.MultiParameter):
    """maximum soil moisture storage [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

class SEAv(parametertools.MultiParameter):
    """easily available soil moisture [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

class IA(parametertools.SingleParameter):
    """percentage of irrigated/total area [-]"""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)

class MOY(parametertools.IndexParameter):
    """References the "global" month of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, 11)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of globwat, indirectly defined by the user."""
    _PARCLASSES = (SMax, SEAv, IA, MOY)
