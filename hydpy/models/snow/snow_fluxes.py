# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.snow import snow_sequences


class Precipitation(snow_sequences.FluxSequence1D):
    """ToDo [mm/T]."""


class Throughfall(snow_sequences.FluxSequence1D):
    """ToDo [mm/T]."""


class ActualMelt(snow_sequences.FluxSequence2D):
    """ToDo [mm/T]."""


class SPL(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution loss of the snow's ice content [mm/T]."""


class WCL(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution loss of the snow's water content [mm/T]."""


class SPG(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution gain of the snow's ice content [mm/T]."""


class WCG(snow_sequences.FluxSequence1D):
    """Subbasin-internal redistribution gain of the snow's water content [mm/T]."""


class Release(snow_sequences.FluxSequence1D):
    """ToDo [mm/T]."""


class PLayer(snow_sequences.Flux1DNLayers):
    """Precipitation of each snow layer [mm/T]."""


class PSnowLayer(snow_sequences.Flux1DNLayers):
    """Snowfall of each snow layer [mm/T]."""


class PRainLayer(snow_sequences.Flux1DNLayers):
    """Rainfall of each snow layer [mm/T]."""


class PotentialMelt(snow_sequences.Flux1DNLayers):
    """Potential snow melt of each snow layer [mm/T]."""


class Melt(snow_sequences.Flux1DNLayers):
    """Actual snow melt of each snow layer [mm/T]."""


class Refr(snow_sequences.FluxSequence2D):
    """Actual (re)freezing of liquid water stored in the snow layer [mm/T]."""


class PNetLayer(snow_sequences.Flux1DNLayers):
    """Net precipitation of each snow layer [mm/T]."""


class PNet(sequencetools.FluxSequence):
    """Net precipitation of the complete catchment [mm/T]."""

    NDIM: Final[Literal[0]] = 0
