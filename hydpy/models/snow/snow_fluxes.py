# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from snow
from hydpy.models.snow import snow_sequences


class PLayer(snow_sequences.Flux1DNLayers):
    """Precipitation of each snow layer [mm/T]."""


class PSnowLayer(snow_sequences.Flux1DNLayers):
    """Snowfall of each snow layer [mm/T]."""


class PRainLayer(snow_sequences.Flux1DNLayers):
    """Rainfall of each snow layer [mm/T]."""


class PotMelt(snow_sequences.Flux1DNLayers):
    """Potential snow melt of each snow layer [mm/T]."""


class Melt(snow_sequences.Flux1DNLayers):
    """Actual snow melt of each snow layer [mm/T]."""


class PNetLayer(snow_sequences.Flux1DNLayers):
    """Net precipitation of each snow layer [mm/T]."""


class PNet(sequencetools.FluxSequence):
    """Net precipitation of the complete catchment [mm/T]."""

    NDIM, NUMERIC = 0, False
