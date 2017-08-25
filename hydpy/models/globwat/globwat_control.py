# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.globwat import globwat_constants
from hydpy.models.globwat import globwat_parameters


class NmbGrids(parametertools.SingleParameter):
    """Number of grids (hydrological response units) in a subbasin [-].

    Note that :class:`NmbGrids` determines the length of most 1-dimensional
    globwat parameters. This required that the value of the respective
    :class:`NmbGrids` instance is set before any of the values of these
    1-dimensional parameters are set. Changing the value of the
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
                if (par.NDIM == 1) and (name != 'moy'):
                    par.shape = self.value
        for (_name, subseqs) in self.subpars.pars.model.sequences:
            for (name, seq) in subseqs:
                if (seq.NDIM == 1) and (name != 'q'):
                    seq.shape = self.value


class VegetationClass(parametertools.MultiParameter):
    """Type of each vegetation class [-].

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
    14 (irrigation germany),
    15 (irrigation czech rebublic),
    16 (irrigation austria),
    17 (irrigation poland),
    18 (irrigation hungary),
    19 (irrigation switzerland),
    20 (irrigation italy),
    21 (irrigation slovenia),
    22 (irrigation croatia),
    23 (irrigation bosnia and herzegovina),
    24 (irrigation albania),
    25 (irrigation serbia),
    26 (irrigation slovakia),
    27 (irrigation ukraine),
    28 (irrigation bulgaria),
    29 (irrigation romania),
    30 (irrigation moldovia),
    31 (other).

    For increasing legibility, the GlobWat constants are used for string
    representions of :class:`VegetationClass` instances:

    >>> from hydpy.models.globwat import *
    >>> parameterstep('1d')
    >>> nmbgrids(4)
    >>> vegetationclass(DESERT, RADRYTROP, RADRYTROP, OTHER)
    >>> vegetationclass.values
    array([10,  1,  1, 31])
    >>> vegetationclass
    vegetationclass(DESERT, RADRYTROP, RADRYTROP, OTHER)
    """
    NDIM, TYPE, TIME, SPAN = 1, int, None, (1, 31)

    def compressrepr(self):
        """Returns a list which contains a string representation with land
        uses beeing defined by the GlobWat constants.
        """
        invmap = {value: key for key, value in
                  globwat_constants.CONSTANTS.items()}
        return [', '.join(invmap.get(value, repr(value))
                          for value in self.values)]


class SCMax(parametertools.MultiParameter):
    """maximum soil moisture capacity [mm/m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class RtD(parametertools.MultiParameter):
    """rooting depth [m]

    Globwat standard value = 0.6."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    # INIT = .6


class RMax(parametertools.MultiParameter):
    """maximum groundwater recharge flux [mm/day]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class Area(parametertools.MultiParameter):
    """area per grid cell [km²]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class KC(globwat_parameters.LanduseMonthParameter):
    """crop or landuse factor [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)


class F(parametertools.SingleParameter):
    """response factor [-].

    Globwat standard value = 0.3.
    """
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)
    INIT = .3


class ROFactor(parametertools.SingleParameter):
    """Factor for turning rain into dirct runoff [-]

    GlobWat standard value = 0.05."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = .05


class ControlParameters(parametertools.SubParameters):
    _PARCLASSES = (NmbGrids, VegetationClass, SCMax, RtD, RMax, Area, KC, F,
                   ROFactor)
