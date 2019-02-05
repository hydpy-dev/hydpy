# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools
# ...from hland
from hydpy.core import objecttools
from hydpy.models.hland import hland_constants
from hydpy.models.hland import hland_parameters


class Area(parametertools.SingleParameter):
    """Subbasin area [km²]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NmbZones(parametertools.SingleParameter):
    """Number of zones (hydrological response units) in a subbasin [-].

    Note that |NmbZones| determines the length of most 1-dimensional
    HydPy-H-Land parameters and sequences.  This required that the value of
    the respective |NmbZones| instance is set before any of the values
    of these 1-dimensional parameters or sequences are set.  Changing the
    value of the |NmbZones| instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(5)
        >>> icmax.shape
        (5,)
        >>> states.ic.shape
        (5,)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to |NmbZones| instances within
        parameter control files.  Sets the shape of most 1-dimensional
        parameter objects (except |UH|) and sequence objects (except |QUH|)
        additionally.
        """
        parametertools.SingleParameter.__call__(self, *args, **kwargs)
        for subpars in self.subpars.pars.model.parameters:
            for par in subpars:
                if (par.NDIM > 0) and (par.name != 'uh'):
                    par.shape = self.value
        for subseqs in self.subpars.pars.model.sequences:
            for seq in subseqs:
                if (seq.NDIM > 0) and (seq.name != 'quh'):
                    seq.shape = self.value


class ZoneType(parametertools.NameParameter):
    """Type of each zone.

    For increasing legibility, the HydPy-H-Land constants are used for
    string representions of |ZoneType| objects:

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(6)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, FIELD)
    >>> zonetype.values
    array([1, 2, 3, 4, 4, 1])
    >>> zonetype
    zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, FIELD)
    """
    NDIM, TYPE, TIME = 1, int, None
    SPAN = (min(hland_constants.CONSTANTS.values()),
            max(hland_constants.CONSTANTS.values()))
    CONSTANTS = hland_constants.CONSTANTS


class ZoneArea(hland_parameters.ParameterComplete):
    """Zone area [km²]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class ZoneZ(hland_parameters.ParameterComplete):
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


class PCorr(hland_parameters.ParameterComplete):
    """General precipitation correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class PCAlt(hland_parameters.ParameterComplete):
    """Elevation correction factor for precipitation [-1/100m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class RfCF(hland_parameters.ParameterComplete):
    """Rainfall correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class SfCF(hland_parameters.ParameterComplete):
    """Snowfall correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class TCAlt(hland_parameters.ParameterComplete):
    """Elevation correction factor for temperature [-1°C/100m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class ECorr(hland_parameters.ParameterNoGlacier):
    """General evaporation correction factor [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class ECAlt(hland_parameters.ParameterNoGlacier):
    """Elevation correction factor for evaporation [-1/100m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class EPF(hland_parameters.ParameterNoGlacier):
    """Decrease in potential evaporation due to precipitation [T/mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, False, (0., None)


class ETF(hland_parameters.ParameterNoGlacier):
    """Temperature factor for evaporation [1/°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class ERed(hland_parameters.ParameterSoil):
    """Factor for restricting actual to potential evaporation [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)


class TTIce(hland_parameters.ParameterLake):
    """Temperature threshold for lake evaporation [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class IcMax(hland_parameters.ParameterSoil):
    """Maximum interception storage [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class TT(hland_parameters.ParameterComplete):
    """Temperature threshold for snow/rain [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class TTInt(hland_parameters.ParameterComplete):
    """Temperature interval with a mixture of snow and rain [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class DTTM(hland_parameters.ParameterLand):
    """Difference between |TTM| and |TT| [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class CFMax(hland_parameters.ParameterLand):
    """Degree day factor for snow (on glaciers or not) [mm/°C/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)


class GMelt(hland_parameters.ParameterGlacier):
    """Degree day factor for glacial ice [mm/°C/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)


class CFR(hland_parameters.ParameterLand):
    """Refreezing factor for water stored within the snow layer [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class WHC(hland_parameters.ParameterLand):
    """Relative water holding capacity of the snow layer [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class FC(hland_parameters.ParameterSoil):
    """Maximum soil moisture content (field capacity) [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class LP(hland_parameters.ParameterSoil):
    """Relative limit for potential evaporation [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)


class Beta(hland_parameters.ParameterSoil):
    """Nonlinearity parameter of the soil routine [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class CFlux(hland_parameters.ParameterSoil):
    """Capacity (maximum) of the capillary return flux [mm/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)


class RespArea(parametertools.SingleParameter):
    """Flag to enable the contributing area approach [-]."""
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

    In addition to the |SingleParameter| call method, it is possible to
    set the value of parameter |K| in accordance to the keyword arguments
    `khq`, `hq` and (optionally) `alpha`.  If `alpha` is not given, the
    value of the respective |Alpha| instance is taken.  This requires the
    |Alpha| instance to be initialized beforehand.

    Basic Equation:
        :math:`K = \\frac{HQ}{(HQ/KHQ)^{1+Alpha}}`

    Examples:

        When directly setting the value of parameter k, one only needs to be
        aware of its time dependence:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> k(2.0)
        >>> k
        k(2.0)
        >>> k.value
        1.0

        Alternatively, one can specify the following three keyword
        arguments directly,...

        >>> k(hq=10.0, khq=2.0, alpha=1.0)
        >>> k
        k(0.4)
        >>> k.value
        0.2

        ...or define the value of parameter alpha beforehand:

        >>> alpha(2.0)
        >>> k(hq=10.0, khq=2.0)
        >>> k
        k(0.08)
        >>> k.value
        0.04

        The following exceptions occur for wrong combinations of
        keyword arguments or when |Alpha| has not been prepared
        beforehand (still has the value |numpy.nan|):

        >>> k(wrong=1)
        Traceback (most recent call last):
        ...
        ValueError: For parameter `k` of element `?` a value can be set \
directly or indirectly by using the keyword arguments `khq` and `hq`.

        >>> k(hq=10.0)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `k` of \
element `?`, at least the keywords arguments `khq` and `hq` must be given.

        >>> import numpy
        >>> alpha(numpy.nan)
        >>> k(hq=10.0, khq=2.0)
        Traceback (most recent call last):
        ...
        RuntimeError: For the alternative calculation of parameter `k` of \
element `?`, either the keyword argument `alpha` must be given or the value \
of parameter `alpha` must be defined beforehand.
    """
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)

    def __call__(self, *args, **kwargs):
        try:
            parametertools.SingleParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            counter = ('khq' in kwargs) + ('hq' in kwargs)
            if counter == 0:
                raise ValueError(
                    f'For parameter {objecttools.elementphrase(self)} a '
                    f'value can be set directly or indirectly by using '
                    f'the keyword arguments `khq` and `hq`.')
            elif counter == 1:
                raise ValueError(
                    f'For the alternative calculation of parameter '
                    f'{objecttools.elementphrase(self)}, at least the '
                    f'keywords arguments `khq` and `hq` must be given.')
            elif counter == 2:
                alpha = float(kwargs.get('alpha', self.subpars.alpha.value))
                if numpy.isnan(alpha):
                    raise RuntimeError(
                        f'For the alternative calculation of parameter '
                        f'{objecttools.elementphrase(self)}, either the '
                        f'keyword argument `alpha` must be given or the value '
                        f'of parameter `alpha` must be defined beforehand.')
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
    """Control parameters of HydPy-H-Land, directly defined by the user."""
    CLASSES = (Area,
               NmbZones,
               ZoneType,
               ZoneArea,
               ZoneZ,
               ZRelP,
               ZRelT,
               ZRelE,
               PCorr,
               PCAlt,
               RfCF,
               SfCF,
               TCAlt,
               ECorr,
               ECAlt,
               EPF,
               ETF,
               ERed,
               TTIce,
               IcMax,
               TT,
               TTInt,
               DTTM,
               CFMax,
               GMelt,
               CFR,
               WHC,
               FC,
               LP,
               Beta,
               PercMax,
               CFlux,
               RespArea,
               RecStep,
               Alpha,
               K,
               K4,
               Gamma,
               MaxBaz,
               Abstr)
