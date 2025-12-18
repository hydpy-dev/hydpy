# pylint: disable=missing-module-docstring

# import...
# ...from snow
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
