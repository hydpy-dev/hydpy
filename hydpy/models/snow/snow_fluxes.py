# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.snow import snow_sequences


class Throughfall(snow_sequences.FluxSequence1D):
    """Frozen or liquid throughfall reaching the snow layer [mm/T]."""


class PotentialMelt(snow_sequences.FluxSequence1D):
    """Potential melting of frozen water stored in the snow layer [mm/T]."""


class ActualMelt(snow_sequences.FluxSequence2D):
    """Actual melting of frozen water stored in the snow layer [mm/T]."""


class PotentialFreeze(snow_sequences.FluxSequence1D):
    """Potential (re)freezing of liquid water stored in the snow layer [mm/T]."""


class ActualFreeze(snow_sequences.FluxSequence2D):
    """Actual (re)freezing of liquid water stored in the snow layer [mm/T]."""


class IceLoss(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution loss of the snow's ice content [mm/T]."""


class WaterLoss(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution loss of the snow's water content [mm/T]."""


class IceGain(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution gain of the snow's ice content [mm/T]."""


class WaterGain(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution gain of the snow's water content [mm/T]."""


class Release(snow_sequences.FluxSequence1D):
    """Release of melted snow water or, if no snow layer exists, throughfall [mm/T]."""


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

    NDIM: Final[Literal[0]] = 0
