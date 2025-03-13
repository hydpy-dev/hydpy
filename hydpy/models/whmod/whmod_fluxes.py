# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools

from hydpy.models.whmod import whmod_sequences


class InterceptionEvaporation(whmod_sequences.Flux1DNonWaterSequence):
    """Evaporation from the interception storage [mm/T]."""


class Throughfall(whmod_sequences.Flux1DNonWaterSequence):
    """Precipitation, passing the interception storage [mm/T]."""


class PotentialSnowmelt(whmod_sequences.Flux1DNonWaterSequence):
    """Potential snowmelt [mm/T]."""


class Snowmelt(whmod_sequences.Flux1DNonWaterSequence):
    """Actual snowmelt [mm/T]."""


class Ponding(whmod_sequences.Flux1DNonWaterSequence):
    """Ponding on land surfaces [mm/T]."""


class SurfaceRunoff(whmod_sequences.Flux1DNonWaterSequence):
    """Surface runoff [mm/T]."""


class Percolation(whmod_sequences.Flux1DSoilSequence):
    """Percolation out of the soil storage [mm/T]."""


class SoilEvapotranspiration(whmod_sequences.Flux1DSoilSequence):
    """Evapotranspiration from the soil storage [mm/T]."""


class LakeEvaporation(whmod_sequences.FluxSequence1DWaterSequence):
    """Evaporation from water areas [mm/T]."""


class TotalEvapotranspiration(whmod_sequences.Flux1DCompleteSequence):
    """Total evapotranspiration [mm/T]."""


class CapillaryRise(whmod_sequences.Flux1DSoilSequence):
    """Capillary rise [mm/T]."""


class RequiredIrrigation(whmod_sequences.Flux1DSoilSequence):
    """Required irrigation [mm/T]."""


class ExternalIrrigation(whmod_sequences.Flux1DSoilSequence):
    """Actual irrigation from external sources [mm/T]."""


class PotentialRecharge(whmod_sequences.Flux1DGroundwaterSequence):
    """Potential recharge [mm/T]."""


class Baseflow(whmod_sequences.Flux1DGroundwaterSequence):
    """Baseflow [mm/T]."""


class ActualRecharge(sequencetools.FluxSequence):
    """Actual recharge [mm/T]."""

    NDIM, NUMERIC = 0, False


class DelayedRecharge(sequencetools.FluxSequence):
    """Delayed recharge [mm/T]."""

    NDIM, NUMERIC = 0, False
