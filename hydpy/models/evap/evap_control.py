# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.models.evap import evap_parameters


class NmbHRU(parametertools.Parameter):
    """The number of separately modelled hydrological response units [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs):
        nmbhru_old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        nmbhru_new = self.value
        if nmbhru_new != nmbhru_old:
            for subpars in self.subpars.pars:
                for par in subpars:
                    if (par.NDIM == 1) and not isinstance(
                        par, parametertools.KeywordParameter1D
                    ):
                        par.shape = nmbhru_new
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.shape = nmbhru_new


class HRUType(parametertools.NameParameter):
    """Hydrological response unit type [-]."""

    NDIM, TYPE, TIME = 1, int, None
    SPAN = (None, None)
    constants = parametertools.Constants(ANY=1)


class HRUArea(parametertools.Parameter):
    """The area of each hydrological response unit [km²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class HRUAltitude(evap_parameters.ZipParameter1D):
    """The altitude of each hydrological response unit [m]."""

    TYPE, TIME, SPAN = float, None, (None, None)
    INIT = 0.0


class MeasuringHeightWindSpeed(parametertools.Parameter):
    """The height above ground of the wind speed measurements [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)
    INIT = 10.0


class AirTemperatureAddend(evap_parameters.ZipParameter1D):
    """Adjustment addend for air temperature [K]."""

    TYPE, TIME, SPAN = float, None, (None, None)
    INIT = 0.0


class CoastFactor(evap_parameters.ZipParameter1D):
    """The "coast factor" of Turc-Wendling's reference evapotranspiration equation
    [-]."""

    TYPE, TIME, SPAN = float, None, (0.6, 1.0)
    INIT = 1.0


class EvapotranspirationFactor(evap_parameters.ZipParameter1D):
    """The adjustment factor for potential evapotranspiration [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 1.0


class MonthFactor(parametertools.MonthParameter):
    """Factor for converting general potential evaporation or evapotranspiration
    (usually grass reference evapotranspiration) to month-specific potential
    evaporation or evapotranspiration [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class LandMonthFactor(evap_parameters.LandMonthParameter):
    """Factor for converting general potential evaporation or evapotranspiration
    (usually grass reference evapotranspiration) to land-use- and month-specific
    potential evaporation or evapotranspiration [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)


class AltitudeFactor(evap_parameters.ZipParameter1D):
    """Decrease of potential evapotranspiration with altitude [-1/100m].

    In the terminology of HBV96: ECAlt."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.1


class PrecipitationFactor(evap_parameters.ZipParameter1D):
    """Decrease in potential evapotranspiration due to precipitation [T/mm].

    In the terminology of HBV96: EPF.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, False, (0.0, None)
    INIT = 0.0


class AirTemperatureFactor(evap_parameters.ZipParameter1D):
    """Temperature factor related to the difference of current reference
    evapotranspiration and normal reference evapotranspiration [1/°C].

    In the terminology of HBV96: ETF.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.1
