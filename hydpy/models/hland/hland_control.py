# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.framework import parametertools
# ...model specific
from hydpy.models.hland import hland_constants
from hydpy.models.hland import hland_parameters


class Area(parametertools.SingleParameter):
    """Subbasin area [km²]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)

class NmbZones(parametertools.SingleParameter):
    """Number of zones (hydrological response units) in a subbasin [-].

    Note that :class:`NmbZones` determines the length of most 1-dimensional
    hland parameters.  This required that the value of the respective
    :class:`NmbZones` instance is set before any of the values of these
    1-dimensional parameters are set.  Changing the value of the
    :class:`NmbZones` instance necessitates setting their values again.

    Examples:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(5)
        >>> model.parameters.control.icmax.shape
        (5,)
        >>> model.sequences.states.ic.shape
        (5,)

    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to :class:`NmbZones` instances
        within parameter control files.  Sets the shape of most 1-dimensional
        parameter objects (except :class:`UH`) and sequence objects (except
        :class:`QUH`) additionally.
        """
        parametertools.SingleParameter.__call__(self, *args, **kwargs)
        for (_name, subpars) in self.subpars.pars.model.parameters:
            for (name, par) in subpars:
                if (par.NDIM > 0) and (name != 'uh'):
                    par.shape = self.value
        for (_name, subseqs) in self.subpars.pars.model.sequences:
            for (name, seq) in subseqs:
                if (seq.NDIM > 0) and (name != 'quh'):
                    seq.shape = self.value

class ZoneType(hland_parameters.MultiParameter):
    """Type of each zone: 1 (FIELD), 2 (FOREST), 3 (GLACIER), or 4 (ILAKE).

    For increasing legibility, the HydPy-H-Land constants are used for string
    representions of :class:`ZoneType` instances:

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(8)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, GLACIER, FOREST, FIELD)
    >>> zonetype.values
    array([1, 2, 3, 4, 4, 3, 2, 1])
    >>> zonetype
    zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, GLACIER, FOREST, FIELD)

    """
    NDIM, TYPE, TIME, SPAN = 1, int, None, (1, 4)

    def compressrepr(self):
        """Returns a list which contains a string representation with zone
        types beeing defined by the constants `FIELD`, `FOREST`...
        """
        result = ', '.join(str(value) for value in self.values)
        for (key, value) in hland_constants.CONSTANTS.iteritems():
            result = result.replace(str(value), key)
        return [result]

class ZoneArea(hland_parameters.MultiParameter):
    """Zone area [km²]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class ZoneZ(hland_parameters.MultiParameter):
    """Zone elevation [100m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class ZRelT(parametertools.SingleParameter):
    """Subbasin-wide reference elevation level for temperature [100m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

class ZRelP(parametertools.SingleParameter):
    """Subbasin-wide reference elevation level for precipitation [100m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

class ZRelE(parametertools.SingleParameter):
    """Subbasin-wide reference elevation level for evaporation [100m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

class PCorr(hland_parameters.MultiParameter):
    """General precipitation correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class PCAlt(hland_parameters.MultiParameter):
    """Elevation correction factor for precipitation [-1/100m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class RfCF(hland_parameters.MultiParameter):
    """Rainfall correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class SfCF(hland_parameters.MultiParameter):
    """Snowfall correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class TCAlt(hland_parameters.MultiParameter):
    """Elevation correction factor for temperature [-1°C/100m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class ECorr(hland_parameters.MultiParameterNoGlacier):
    """General evaporation correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class ECAlt(hland_parameters.MultiParameterNoGlacier):
    """Elevation correction factor for evaporation [-1/100m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class EPF(hland_parameters.MultiParameterNoGlacier):
    """Decrease in potential evaporation due to precipitation [T/mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, False, (0., None)

class ETF(hland_parameters.MultiParameterNoGlacier):
    """Temperature factor for evaporation [1/°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class ERed(hland_parameters.MultiParameterSoil):
    """Factor for restricting actual to potential evaporation [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)

class TTIce(hland_parameters.MultiParameterLake):
    """Temperature threshold for lake evaporation [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class IcMax(hland_parameters.MultiParameterSoil):
    """Maximum interception storage [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class TT(hland_parameters.MultiParameter):
    """Temperature threshold for snow/rain [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class TTInt(hland_parameters.MultiParameter):
    """Temperature interval with a mixture of snow and rain [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class DTTM(hland_parameters.MultiParameterLand):
    """Difference between :class:`TTM` and :class:`TT` [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class CFMax(hland_parameters.MultiParameterLand):
    """Degree day factor for snow (on glaciers or not) [mm/°C/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)

class GMelt(hland_parameters.MultiParameterGlacier):
    """Degree day factor for glacial ice [mm/°C/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)

class CFR(hland_parameters.MultiParameterLand):
    """Refreezing factor for water stored within the snow layer [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class WHC(hland_parameters.MultiParameterLand):
    """Relative water holding capacity of the snow layer [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class FC(hland_parameters.MultiParameterSoil):
    """Maximum soil moisture content (field capacity) [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class LP(hland_parameters.MultiParameterSoil):
    """Relative limit for potential evaporation [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)

class Beta(hland_parameters.MultiParameterSoil):
    """Nonlinearity parameter of the soil routine [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class CFlux(hland_parameters.MultiParameterSoil):
    """Capacity (maximum) of the capillary return flux [mm/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)

class RespArea(parametertools.SingleParameter):
    """Flag to enable the contibuting area approach [-]."""
    NDIM, TYPE, TIME, SPAN = 0, bool, None, (0., None)

class RecStep(parametertools.SingleParameter):
    """Number of internal computation steps per simulation time step [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, True, (1, None)

    def __call__(self, *args, **kwargs):
        parametertools.SingleParameter.__call__(self, *args, **kwargs)
        self.value = int(round(self.value))

class PercMax(parametertools.SingleParameter):
    """Maximum percolation rate [mm/T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)

class K(parametertools.SingleParameter):
    """Recession coefficient of the upper zone layer [1/T/mm^alpha].


    In addition to the :class:`parametertools.SingleParameter` call method, it
    is possible to set the value of parameter :class:`K` in accordance to
    the keyword arguments `khq`, `hq` and (optionally) `alpha`.  If `alpha`
    is not given, the value of the respective :class:`Alpha` instance is
    taken.  This requires the :class:`Alpha` instance to be initialized
    beforehand.

    Basic Equation:
        :math:`K = \\frac{HQ}{(HQ/KHQ)^{1+Alpha}}`

    Examples:

        When directly setting the value of parameter k, one only needs to be
        aware of its time dependence:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h', warn=False)
        >>> k(2.)
        >>> k
        k(2.0)
        >>> k.value
        1.0

        Alternatively, one can specify the following three keyword
        arguments directly,...


        >>> k(hq=10., khq=2., alpha=1.)
        >>> k
        k(0.4)
        >>> k.value
        0.2

        ...or define the value of parameter alpha beforehand:

        >>> alpha(2.)
        >>> k(hq=10., khq=2.)
        >>> k
        k(0.08)
        >>> k.value
        0.04

    """
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`K` instances
        within parameter control files.
        """
        try:
            parametertools.SingleParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            counter = ('khq' in kwargs) + ('hq' in kwargs)
            if counter == 0:
                raise ValueError('For parameter `k` a value can be set '
                                 'directly or indirectly by using the '
                                 'keyword arguments `khq` and `hq`.')
            elif counter == 1:
                raise ValueError('For the alternative calculation of '
                                 'parameter `k`, at least the keywords '
                                 'arguments `khq` and `hq` must be given.')
            elif counter == 2:
                try:
                    alpha = float(kwargs['alpha'])
                except KeyError:
                    try:
                        alpha = self.subpars.alpha.value
                    except (AttributeError, RuntimeError):
                        raise RuntimeError('For the alternative calculation '
                                           'of parameter `k`, either the '
                                           'keyword argument `alpha` must be '
                                           'given or the value of parameter '
                                           '`alpha` must be defined '
                                           'beforehand.')
                khq = float(kwargs['khq'])
                hq = float(kwargs['hq'])
                self(hq/((hq/khq)**(alpha+1.)))

class Alpha(parametertools.SingleParameter):
    """Nonlinearity parameter of the upper zone layer [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class K4(parametertools.SingleParameter):
    """Recession coefficient of the lower zone layer [1/T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)

class Gamma(parametertools.SingleParameter):
    """Nonlinearity parameter of the lower zone layer [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class MaxBaz(parametertools.SingleParameter):
    """Base length of the triangle unit hydrograph [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)

class Abstr(parametertools.SingleParameter):
    """Abstraction of water from computed outflow [mm/T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, True, (None, None)

class ControlParameters(parametertools.SubParameters):
    """Control parameters of hland, directly defined by the user."""
    _PARCLASSES = (Area, NmbZones, ZoneType, ZoneArea, ZoneZ, ZRelP, ZRelT,
                   ZRelE, PCorr, PCAlt, RfCF, SfCF, TCAlt, ECorr, ECAlt, EPF,
                   ETF, ERed, TTIce, IcMax, TT, TTInt, DTTM, CFMax, GMelt, CFR,
                   WHC, FC, LP, Beta, PercMax, CFlux, RespArea, RecStep, Alpha,
                   K, K4, Gamma, MaxBaz, Abstr)
