# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.evap import evap_sequences


class MeanAirTemperature(sequencetools.FactorSequence):
    """The basin's mean air temperature [°C]."""

    NDIM: Final[Literal[0]] = 0


class AirTemperature(evap_sequences.FactorSequence1D):
    """Air temperature [°C]."""


class DailyAirTemperature(evap_sequences.FactorSequence1D):
    """The average air temperature in the last 24 hours [°C]."""


class WindSpeed2m(sequencetools.FactorSequence):
    """Wind speed at 2 m above grass-like vegetation [m/s]."""

    NDIM: Final[Literal[0]] = 0


class DailyWindSpeed2m(sequencetools.FactorSequence):
    """Average wind speed 2 meters above ground in the last 24 hours [m/s]."""

    NDIM: Final[Literal[0]] = 0


class WindSpeed10m(sequencetools.FactorSequence):
    """Wind speed at 10 m above grass-like vegetation [m/s]."""

    NDIM: Final[Literal[0]] = 0


class DailyRelativeHumidity(sequencetools.FactorSequence):
    """Average relative humidity in the last 24 hours [%]."""

    NDIM: Final[Literal[0]] = 0


class SunshineDuration(sequencetools.FactorSequence):
    """Sunshine duration [h]."""

    NDIM: Final[Literal[0]] = 0


class PossibleSunshineDuration(sequencetools.FactorSequence):
    """Astronomically possible sunshine duration [h]."""

    NDIM: Final[Literal[0]] = 0


class DailySunshineDuration(sequencetools.FactorSequence):
    """The actual sunshine duration in the last 24 hours [h]."""

    NDIM: Final[Literal[0]] = 0


class DailyPossibleSunshineDuration(sequencetools.FactorSequence):
    """The astronomically possible sunshine duration in the last 24 hours [h]."""

    NDIM: Final[Literal[0]] = 0


class SaturationVapourPressure(evap_sequences.FactorSequence1D):
    """Saturation vapour pressure [hPa]."""


class DailySaturationVapourPressure(evap_sequences.FactorSequence1D):
    """Average saturation vapour pressure in the last 24 hours [hPa]."""


class SaturationVapourPressureSlope(evap_sequences.FactorSequence1D):
    """The slope of the saturation vapour pressure curve [hPa/K]."""


class DailySaturationVapourPressureSlope(evap_sequences.FactorSequence1D):
    """Average saturation vapour pressure slope in the last 24 hours [hPa/K]."""


class ActualVapourPressure(evap_sequences.FactorSequence1D):
    """Actual vapour pressure [hPa]."""


class DailyActualVapourPressure(evap_sequences.FactorSequence1D):
    """The average actual vapour pressure in the last 24 hours [hPa]."""


class DryAirPressure(evap_sequences.FactorSequence1D):
    """Dry air pressure [hPa]."""


class AirDensity(evap_sequences.FactorSequence1D):
    """Air density [kg/m³]."""


class PsychrometricConstant(sequencetools.FactorSequence):
    """Psychrometric constant [hPa/K]."""

    NDIM: Final[Literal[0]] = 0


class CurrentAlbedo(evap_sequences.FactorSequence1D):
    """The current albedo of the relevant surface [-]."""


class AdjustedCloudCoverage(sequencetools.FactorSequence):
    """Adjusted degree of cloud coverage [-]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, 1.0)


class AerodynamicResistance(evap_sequences.FactorSequence1D):
    """Aerodynamic resistance [s/m]."""


class SoilSurfaceResistance(evap_sequences.FactorSequence1D):
    """Soil surface resistance [s/m]."""


class LanduseSurfaceResistance(evap_sequences.FactorSequence1D):
    """Surface resistance for the current moisture conditions of water areas, sealed
    areas, and vegetation [s/m]."""


class ActualSurfaceResistance(evap_sequences.FactorSequence1D):
    """Actual surface resistance [s/m]."""


class InterceptedWater(evap_sequences.FactorSequence1D):
    """Intercepted water [mm]."""


class SoilWater(evap_sequences.FactorSequence1D):
    """Soil water content [mm]."""


class SnowCover(evap_sequences.FactorSequence1D):
    """Snow cover degree [-]."""


class SnowyCanopy(evap_sequences.FactorSequence1D):
    """Snow cover degree in the canopies of tree-like vegetation (is for |numpy.nan|
    non-tree-like vegetation) [-]."""
