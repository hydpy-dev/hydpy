# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.evap import evap_sequences


class MeanAirTemperature(sequencetools.FactorSequence):
    """The basin's mean air temperature [°C]."""

    NDIM, NUMERIC = 0, False


class AirTemperature(evap_sequences.FactorSequence1D):
    """Air temperature [°C]."""

    NUMERIC = False


class DailyAirTemperature(evap_sequences.FactorSequence1D):
    """The average air temperature in the last 24 hours [°C]."""

    NUMERIC = False


class WindSpeed2m(sequencetools.FactorSequence):
    """Wind speed at 2 m above grass-like vegetation [m/s]."""

    NDIM, NUMERIC = 0, False


class DailyWindSpeed2m(sequencetools.FactorSequence):
    """Average wind speed 2 meters above ground in the last 24 hours [m/s]."""

    NDIM, NUMERIC = 0, False


class WindSpeed10m(sequencetools.FactorSequence):
    """Wind speed at 10 m above grass-like vegetation [m/s]."""

    NDIM, NUMERIC = 0, False


class AdjustedWindSpeed10m(sequencetools.FactorSequence):
    """Land cover-specific wind speed at 10 m above ground (or zero plane displacement)
    [m/s]."""

    NDIM, NUMERIC = 1, False


class DailyRelativeHumidity(sequencetools.FactorSequence):
    """Average relative humidity in the last 24 hours [%]."""

    NDIM, NUMERIC = 0, False


class SunshineDuration(sequencetools.FactorSequence):
    """Sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class DailySunshineDuration(sequencetools.FactorSequence):
    """The actual sunshine duration in the last 24 hours [h]."""

    NDIM, NUMERIC = 0, False


class DailyPossibleSunshineDuration(sequencetools.FactorSequence):
    """The astronomically possible sunshine duration in the last 24 hours [h]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressure(evap_sequences.FactorSequence1D):
    """Saturation vapour pressure [hPa]."""

    NUMERIC = False


class DailySaturationVapourPressure(evap_sequences.FactorSequence1D):
    """Average saturation vapour pressure in the last 24 hours [hPa]."""

    NUMERIC = False


class SaturationVapourPressureSlope(evap_sequences.FactorSequence1D):
    """The slope of the saturation vapour pressure curve [hPa/K]."""

    NUMERIC = False


class DailySaturationVapourPressureSlope(evap_sequences.FactorSequence1D):
    """Average saturation vapour pressure slope in the last 24 hours [hPa/K]."""

    NUMERIC = False


class ActualVapourPressure(evap_sequences.FactorSequence1D):
    """Actual vapour pressure [hPa]."""

    NUMERIC = False


class DailyActualVapourPressure(evap_sequences.FactorSequence1D):
    """The average actual vapour pressure in the last 24 hours [hPa]."""

    NUMERIC = False


class DryAirPressure(evap_sequences.FactorSequence1D):
    """Dry air pressure [hPa]."""

    NUMERIC = False


class AirDensity(evap_sequences.FactorSequence1D):
    """Air density [kg/m³]."""

    NUMERIC = False


class PsychrometricConstant(sequencetools.FactorSequence):
    """Psychrometric constant [hPa/K]."""

    NDIM, NUMERIC = 0, False


class CurrentAlbedo(evap_sequences.FactorSequence1D):
    """The current albedo of the relevant surface [-]."""

    NUMERIC = False


class AdjustedCloudCoverage(sequencetools.FactorSequence):
    """Adjusted degree of cloud coverage [-]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, 1.0)


class AerodynamicResistance(evap_sequences.FactorSequence1D):
    """Aerodynamic resistance [s/m]."""

    NUMERIC = False


class SoilSurfaceResistance(evap_sequences.FactorSequence1D):
    """Soil surface resistance [s/m]."""

    NUMERIC = False


class LanduseSurfaceResistance(evap_sequences.FactorSequence1D):
    """Surface resistance for the current moisture conditions of water areas, sealed
    areas, and vegetation [s/m]."""

    NUMERIC = False


class ActualSurfaceResistance(evap_sequences.FactorSequence1D):
    """Actual surface resistance [s/m]."""

    NUMERIC = False


class InterceptedWater(evap_sequences.FactorSequence1D):
    """Intercepted water [mm]."""

    NUMERIC = False


class SoilWater(evap_sequences.FactorSequence1D):
    """Soil water content [mm]."""

    NUMERIC = False


class SnowCover(evap_sequences.FactorSequence1D):
    """Snow cover degree [-]."""

    NUMERIC = False


class SnowyCanopy(evap_sequences.FactorSequence1D):
    """Snow cover degree in the canopies of tree-like vegetation (is for |numpy.nan|
    non-tree-like vegetation) [-]."""

    NUMERIC = False
