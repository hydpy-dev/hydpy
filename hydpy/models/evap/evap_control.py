# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools


class NmbHRU(parametertools.Parameter):
    """The number of separately modelled hydrological response units [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        nmbhru_old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        nmbhru_new = self.value
        if nmbhru_new != nmbhru_old:
            for subpars in self.subpars.pars:
                for par in subpars:
                    if par.NDIM == 1:
                        par.shape = nmbhru_new
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.shape = nmbhru_new


class HRUArea(parametertools.Parameter):
    """The area of each hydrological response unit [km²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class Altitude(parametertools.Parameter):
    """The altitude of each hydrological response unit [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


class MeasuringHeightWindSpeed(parametertools.Parameter):
    """The height above ground of the wind speed measurements [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)
    INIT = 10.0


class AirTemperatureAddend(parametertools.Parameter):
    """Adjustment addend for air temperature [K]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


class CoastFactor(parametertools.Parameter):
    """The "coast factor" of Turc-Wendling's reference evapotranspiration equation
    [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.6, 1.0)
    INIT = 1.0


class EvapotranspirationFactor(parametertools.Parameter):
    """The adjustment factor for potential evapotranspiration [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 1.0
