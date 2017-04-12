# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.lland import lland_parameters

class RelSubArea(lland_parameters.MultiParameter):
    """Relative Grouped Response Area [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)

class MOY(parametertools.IndexParameter):
    """References the "global" month of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, 11)

class KInz(lland_parameters.LanduseMonthParameter):
    """Interzeptionskapazität bezogen auf die Bodenoberfläche (interception
    capacity normalized to the soil surface area) [mm]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

class WB(lland_parameters.MultiParameter):
    """Absolute Mindestbodenfeuchte für die Basisabflussentstehung (threshold
       value of absolute soil moisture for base flow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class WZ(lland_parameters.MultiParameter):
    """Absolute Mindestbodenfeuchte für die Interflowentstehung (threshold
       value of absolute soil moisture for interflow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class KB(parametertools.SingleParameter):
    """Konzentrationszeit des Basisabflusses (concentration time of baseflow)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class KI1(parametertools.SingleParameter):
    """Konzentrationszeit des "unteren" Zwischenabflusses (concentration time 
    of the first interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class KI2(parametertools.SingleParameter):
    """Konzentrationszeit des "oberen" Zwischenabflusses" (concentration time 
    of the second interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class KD(parametertools.SingleParameter):
    """Konzentrationszeit des Directabflusses (concentration time of direct
    runoff) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    
class QFactor(parametertools.SingleParameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-H-Land, indirectly defined by the user."""
    _PARCLASSES = (RelSubArea, MOY, KInz, WB, WZ, KB, KI1, KI2, KD, QFactor)