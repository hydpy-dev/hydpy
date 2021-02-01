# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.models.wland import wland_parameters
from hydpy.models.wland import wland_constants
from hydpy.models.wland.wland_constants import *


class AL(parametertools.Parameter):
    """Land area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class AS_(parametertools.Parameter):
    """Surface water area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class NU(parametertools.Parameter):
    """Number of hydrological response units [-].

    Parameter |NU| automatically sets the length of most 1-dimensional parameters
    and sequences of *HydPy-W-Land*:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(3)
    >>> lt.shape
    (3,)
    >>> states.ic.shape
    (3,)

    Changing the value of parameter |NU| reshapes the related parameters
    and sequences and thereby eventually deletes predefined values:

    >>> states.ic = 1.0
    >>> states.ic
    ic(1.0, 1.0, 1.0)
    >>> nu(2)
    >>> states.ic
    ic(nan, nan)

    Redefining the same value for parameter |NU| does not affect any related
    parameter and sequence object:

    >>> states.ic = 1.0
    >>> states.ic
    ic(1.0, 1.0)
    >>> nu(2)
    >>> states.ic
    ic(1.0, 1.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs):
        old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new = self.__hydpy__get_value__()
        if new != old:
            for subpars in self.subpars.pars.model.parameters:
                for par in subpars:
                    if (par.NDIM == 1) and (
                        not isinstance(par, parametertools.MonthParameter)
                    ):
                        par.__hydpy__set_shape__(new)
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.__hydpy__set_shape__(new)


class LT(parametertools.NameParameter):
    """Landuse type [-].

    For better readability, use the land-use related constants defined in
    module |wland_constants| to set the individual hydrological response
    units' land-use types:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(11)
    >>> lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE, WETLAND,
    ...    TREES, CONIFER, DECIDIOUS, MIXED)
    >>> lt
    lt(SEALED, FIELD, WINE, ORCHARD, SOIL, PASTURE, WETLAND, TREES,
       CONIFER, DECIDIOUS, MIXED)
    """

    NDIM, TYPE, TIME = 1, int, None
    SPAN = (
        min(wland_constants.LANDUSE_CONSTANTS.values()),
        max(wland_constants.LANDUSE_CONSTANTS.values()),
    )
    CONSTANTS = wland_constants.LANDUSE_CONSTANTS


class AUR(parametertools.Parameter):
    """Relative area of each hydrological response unit [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


class CP(parametertools.Parameter):
    """Factor for correcting precipitation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CPET(parametertools.Parameter):
    """Factor for correcting potential evapotranspiration [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CPETL(wland_parameters.LanduseMonthParameter):
    """Factor for converting general potential evapotranspiration (usually grass
    reference evapotranspiration) to land-use specific potential evapotranspiration
    [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)


class CPES(parametertools.MonthParameter):
    """Factor for converting general potential evapotranspiration (usually grass
    reference evapotranspiration) to potential evaporation from water areas [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class LAI(wland_parameters.LanduseMonthParameter):
    """Leaf area index [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)


class IH(parametertools.Parameter):
    """Interception capacity with respect to the leaf surface area [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class TT(parametertools.Parameter):
    """Threshold temperature for snow/rain [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class TI(parametertools.Parameter):
    """Temperature interval with a mixture of snow and rain [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class DDF(wland_parameters.LanduseParameter):
    """Day degree factor [mm/°C/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)


class DDT(parametertools.Parameter):
    """Day degree threshold temperature [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class CW(parametertools.Parameter):
    """Wetness index parameter [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1.0, None)


class CV(parametertools.Parameter):
    """Vadose zone relaxation time constant [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class CG(parametertools.Parameter):
    """Groundwater reservoir constant [mm T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class CGF(parametertools.Parameter):
    """Groundwater reservoir flood factor [1/mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class CQ(parametertools.Parameter):
    """Quickflow reservoir relaxation time [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)


class CD(parametertools.Parameter):
    """Channel depth [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class CS(parametertools.Parameter):
    """Surface water parameter for bankfull discharge [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)


class HSMin(parametertools.Parameter):
    """Surface water level where and below which discharge is zero [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class XS(parametertools.Parameter):
    """Stage-discharge relation exponent [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5


class B(wland_parameters.SoilParameter):
    """Pore size distribution parameter [-].

    Parameter |B| comes with the following default values:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> b.print_defaults()
    SAND: 4.05
    LOAMY_SAND: 4.38
    SANDY_LOAM: 4.9
    SILT_LOAM: 5.3
    LOAM: 5.39
    SANDY_CLAY_LOAM: 7.12
    SILT_CLAY_LOAM: 7.75
    CLAY_LOAM: 8.52
    SANDY_CLAY: 10.4
    SILTY_CLAY: 10.4
    CLAY: 11.4

    See the documentation on class |SoilParameter| for further information.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    _SOIL2VALUE = {
        SAND: 4.05,
        LOAMY_SAND: 4.38,
        SANDY_LOAM: 4.9,
        SILT_LOAM: 5.3,
        LOAM: 5.39,
        SANDY_CLAY_LOAM: 7.12,
        SILT_CLAY_LOAM: 7.75,
        CLAY_LOAM: 8.52,
        SANDY_CLAY: 10.4,
        SILTY_CLAY: 10.4,
        CLAY: 11.4,
    }


class PsiAE(wland_parameters.SoilParameter):
    """Air entry pressure [mm].

    Parameter |PsiAE| comes with the following default values:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> psiae.print_defaults()
    SAND: 121.0
    LOAMY_SAND: 90.0
    SANDY_LOAM: 218.0
    SILT_LOAM: 786.0
    LOAM: 478.0
    SANDY_CLAY_LOAM: 299.0
    SILT_CLAY_LOAM: 356.0
    CLAY_LOAM: 630.0
    SANDY_CLAY: 153.0
    SILTY_CLAY: 490.0
    CLAY: 405.0

    See the documentation on class |SoilParameter| for further information.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    _SOIL2VALUE = {
        SAND: 121.0,
        LOAMY_SAND: 90.0,
        SANDY_LOAM: 218.0,
        SILT_LOAM: 786.0,
        LOAM: 478.0,
        SANDY_CLAY_LOAM: 299.0,
        SILT_CLAY_LOAM: 356.0,
        CLAY_LOAM: 630.0,
        SANDY_CLAY: 153.0,
        SILTY_CLAY: 490.0,
        CLAY: 405.0,
    }


class ThetaS(wland_parameters.SoilParameter):
    """Soil moisture content at saturation [-].

    Parameter |ThetaS| comes with the following default values:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> thetas.print_defaults()
    SAND: 0.395
    LOAMY_SAND: 0.41
    SANDY_LOAM: 0.435
    SILT_LOAM: 0.485
    LOAM: 0.451
    SANDY_CLAY_LOAM: 0.42
    SILT_CLAY_LOAM: 0.477
    CLAY_LOAM: 0.476
    SANDY_CLAY: 0.426
    SILTY_CLAY: 0.492
    CLAY: 0.482

    See the documentation on class |SoilParameter| for further information.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    _SOIL2VALUE = {
        SAND: 0.395,
        LOAMY_SAND: 0.41,
        SANDY_LOAM: 0.435,
        SILT_LOAM: 0.485,
        LOAM: 0.451,
        SANDY_CLAY_LOAM: 0.42,
        SILT_CLAY_LOAM: 0.477,
        CLAY_LOAM: 0.476,
        SANDY_CLAY: 0.426,
        SILTY_CLAY: 0.492,
        CLAY: 0.482,
    }


class Zeta1(parametertools.Parameter):
    """Curvature parameter of the evapotranspiration reduction function [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.02


class Zeta2(parametertools.Parameter):
    """Inflection point of the evapotranspiration reduction function [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 400.0


class SH(parametertools.Parameter):
    """General smoothing parameter related to the height of water columns [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class ST(parametertools.Parameter):
    """General smoothing parameter related to temperature [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
