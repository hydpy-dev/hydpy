# pylint: disable=missing-module-docstring

import numpy

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.meteo import meteo_parameters
from hydpy.models.meteo import meteo_variables


class NmbHRU(parametertools.NmbParameter):
    """The number of hydrological response units [-]."""

    SPAN = (1, None)


class HRUArea(meteo_variables.MixinHRUs, parametertools.Parameter):
    """The area of each hydrological response unit [km²]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)


class Latitude(parametertools.Parameter):
    """The latitude [decimal degrees]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (-90.0, 90.0)


class Longitude(parametertools.Parameter):
    """The longitude [decimal degrees]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (-180.0, 180.0)


class AngstromConstant(parametertools.MonthParameter):
    """The Ångström "a" coefficient for calculating global radiation [-]."""

    TYPE: Final = float
    SPAN = (0.0, 1.0)
    INIT = 0.25

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim values following :math:`AngstromConstant \leq  1 - AngstromFactor` or
        at least following :math:`AngstromConstant \leq  1`.

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> angstromconstant(1.5)
        >>> angstromconstant
        angstromconstant(1.0)
        >>> angstromfactor.value = 0.6
        >>> angstromconstant(0.5)
        >>> angstromconstant
        angstromconstant(0.4)
        """
        if upper is None:
            upper = self.subpars.angstromfactor.values.copy()
            idxs = numpy.isnan(upper)
            upper[idxs] = 1.0
            upper[~idxs] = 1.0 - upper[~idxs]
        return super().trim(lower, upper)


class AngstromFactor(parametertools.MonthParameter):
    """The Ångström "b" coefficient for calculating global radiation [-]."""

    TYPE: Final = float
    SPAN = (0.0, 1.0)
    INIT = 0.5

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim values in accordance with :math:`AngstromFactor \leq  1 -
        AngstromConstant` or at least in accordance with :math:`AngstromFactor \leq 1`.

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> angstromfactor(1.5)
        >>> angstromfactor
        angstromfactor(1.0)
        >>> angstromconstant.value = 0.6
        >>> angstromfactor(0.5)
        >>> angstromfactor
        angstromfactor(0.4)
        """
        if upper is None:
            upper = self.subpars.angstromconstant.values.copy()
            idxs = numpy.isnan(upper)
            upper[idxs] = 1.0
            upper[~idxs] = 1.0 - upper[~idxs]
        return super().trim(lower, upper)


class AngstromAlternative(parametertools.MonthParameter):
    """An alternative Ångström coefficient for replacing coefficient "c"
    (|AngstromConstant|) on days without any direct sunshine [-]."""

    TYPE: Final = float
    SPAN = (0.0, 1.0)
    INIT = 0.15


class TemperatureAddend(meteo_parameters.ZipParameter1D):
    """Temperature shift constant [°C]."""

    TYPE: Final = float
    INIT = 0.0


class PrecipitationFactor(meteo_parameters.ZipParameter1D):
    """Precipitation adjustment factor [-]."""

    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.0
