# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.globwat import globwat_constants
from hydpy.models.globwat import globwat_parameters


class Area(parametertools.SingleParameter):
    """area of the input grids [km²]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)

class NmbGrids(parametertools.SingleParameter):
    """Number of grids (hydrological response units) in a subbasin [-].

    Note that :class:`NmbGrids` determines the length of most 1-dimensional
    globwat parameters. This required that the value of the respective
    :class:`NmbGrids` instance is set before any of the values of these
    1-dimensional parameters are set.  Changing the value of the
    :class:`NmbGrids` instance necessitates setting their values again.
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to :class:`NmbGrids` instances
        within parameter control files.  Sets the shape of most 1-dimensional
        parameter objects and sequence objects.
        """
        parametertools.SingleParameter.__call__(self, *args, **kwargs)
        for (_name, subpars) in self.subpars.pars.model.parameters:
            for (name, par) in subpars:
                if (par.NDIM==1):# and (name != 'uh'):
                    par.shape = self.value
        for (_name, subseqs) in self.subpars.pars.model.sequences:
            for (name, seq) in subseqs:
                if (seq.NDIM==1):# and (name != 'quh'):
                    seq.shape = self.value

class VegetationClass(parametertools.MultiParameter):
    """Type of each vegetation class:
    1 (rainfed agriculture: dry tropics),
    2 (rainfed agriculture: humid tropics),
    3 (rainfed agriculture: highlands),
    4 (rainfed agriculture: subtropics),
    5 (rainfed agriculture: temperate),
    6 (rangelands: subtropics),
    7 (rangelands: temperate),
    8 (rangelands: boreal),
    9 (forest),
    10 (desert),
    11 (water),
    12 (irrigated crops: paddy rice),
    13 (irrigated crops: other than paddy rice),
    14 (other)."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (1, 14)

    def compressrepr(self):
        """Returns a list which contains a string representation with vegetation
        classes beeing defined by the constants `RADRYTROP`, `RAHUMTROP`...
        """
        result = ', '.join(str(value) for value in self.values)
        for (key, value) in globwat_constants.CONSTANTS.iteritems():
            result = result.replace(str(value), key)
        return [result]

class SCMax(parametertools.MultiParameter):
    """maximum soil moisture capacity [mm/m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class RtD(parametertools.MultiParameter):
    """rooting depth [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class RMax(parametertools.MultiParameter):
    """maximum groundwater recharge flux [mm/day]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class CIc(parametertools.MultiParameter):
    """cropping intensity [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 100.)

class TA (parametertools.MultiParameter):
    """total area [km²]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class IrrA(parametertools.MultiParameter):
    """irrigated area [km²]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class KC(globwat_parameters.LanduseMonthParameter):
    """crop or landuse factor [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

class KOW(globwat_parameters.LanduseMonthParameter):
    """open water factor [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

class PWA(parametertools.SingleParameter):
    """percentual water surface per grid cell [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 100.)

class F(parametertools.SingleParameter):
    """response factor [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (.3, .3)

class ControlParameters(parametertools.SubParameters):
    _PARCLASSES = (Area, NmbGrids, VegetationClass, SCMax, RtD, RMax, CIc, TA, IrrA, KC, KOW, PWA, F)