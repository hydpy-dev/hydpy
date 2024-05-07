# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.models.meteo import meteo_parameters


class NmbHRU(parametertools.Parameter):
    """The number of hydrological response units [-].

    |NmbHRU| determines the length of the 1-dimensional parameters and sequences:

    >>> from hydpy.models.meteo import *
    >>> parameterstep()
    >>> nmbhru(5)
    >>> precipitationfactor.shape
    (5,)
    >>> fluxes.precipitation.shape
    (5,)

    Changing the value of |NmbHRU| later reshapes the affected parameters and sequences
    and makes resetting their values necessary:

    >>> precipitationfactor(2.0)
    >>> precipitationfactor
    precipitationfactor(2.0)
    >>> nmbhru(3)
    >>> precipitationfactor
    precipitationfactor(?)

    Re-defining the same value does not delete the already available data:

    >>> precipitationfactor(2.0)
    >>> nmbhru(3)
    >>> precipitationfactor
    precipitationfactor(2.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs) -> None:
        old_shape = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new_shape = self.value
        if new_shape != old_shape:
            for subpars in self.subpars.pars:
                for par in subpars:
                    if par.NDIM == 1:
                        par.shape = new_shape
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.shape = new_shape


class HRUArea(parametertools.Parameter):
    """The area of each hydrological response unit [km²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class Latitude(parametertools.Parameter):
    """The latitude [decimal degrees]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (-90.0, 90.0)


class Longitude(parametertools.Parameter):
    """The longitude [decimal degrees]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (-180.0, 180.0)


class AngstromConstant(parametertools.MonthParameter):
    """The Ångström "a" coefficient for calculating global radiation [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.25

    def trim(self, lower=None, upper=None) -> bool:
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

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.5

    def trim(self, lower=None, upper=None) -> bool:
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

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.15


class TemperatureAddend(meteo_parameters.ZipParameter1D):
    """Temperature shift constant [°C]."""

    TYPE, TIME, SPAN = float, None, (None, None)
    INIT = 0.0


class PrecipitationFactor(meteo_parameters.ZipParameter1D):
    """Precipitation adjustment factor [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 1.0
