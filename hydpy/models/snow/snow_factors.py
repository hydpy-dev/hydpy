# pylint: disable=missing-module-docstring

from hydpy.models.snow import snow_sequences


class TLayer(snow_sequences.Factor1DNLayers):
    """Mean air temperature of each snow layer [°C]."""


class TMinLayer(snow_sequences.Factor1DNLayers):
    """Minimum air temperature of each snow layer [°C]."""


class TMaxLayer(snow_sequences.Factor1DNLayers):
    """Maximum air temperature of each snow layer [°C]."""


class SolidFractionPrecipitation(snow_sequences.Factor1DNLayers):
    """Solid fraction of precipitation of each snow layer [-]."""

    SPAN = (0.0, 1.0)


class FracRain(snow_sequences.FactorSequence1D):
    """Fraction rainfall / total precipitation [-]."""


class MeltingFactor(snow_sequences.FactorSequence1D):
    """Actual degree day factor for snow (on glaciers or not) [mm/°C/T]."""


class SWE(snow_sequences.FactorSequence1D):
    """Snow water equivalent [mm]."""


class TC(snow_sequences.FactorSequence1D):
    """Corrected temperature [°C]."""
