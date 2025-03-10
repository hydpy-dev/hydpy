# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod import whmod_sequences


class InterceptionEvaporation(whmod_sequences.Flux1DSequence):
    """Evaporation from the interception storage [mm/T]."""


class Throughfall(whmod_sequences.Flux1DSequence):
    """Precipitation, passing the interception storage [mm/T]."""


class PotentialSnowmelt(whmod_sequences.Flux1DSequence):
    """Potential snowmelt [mm/T]."""


class Snowmelt(whmod_sequences.Flux1DSequence):
    """Actual snowmelt [mm/T]."""


class Ponding(whmod_sequences.Flux1DSequence):
    """Ponding on land surfaces [mm/T]."""


class SurfaceRunoff(whmod_sequences.Flux1DSequence):
    """Surface runoff [mm/T]."""


class Percolation(whmod_sequences.Flux1DSequence):
    """Percolation out of the soil storage [mm/T]."""


class SoilEvapotranspiration(whmod_sequences.Flux1DSequence):
    """Evapotranspiration from the soil storage [mm/T]."""


class LakeEvaporation(whmod_sequences.Flux1DSequence):
    """Evaporation from water areas [mm/T]."""


class TotalEvapotranspiration(whmod_sequences.Flux1DSequence):
    """Total evapotranspiration [mm/T]."""


class CapillaryRise(whmod_sequences.Flux1DSequence):
    """Capillary rise [mm/T]."""


class PotentialRecharge(whmod_sequences.Flux1DSequence):
    """Potential recharge [mm/T]."""


class Baseflow(whmod_sequences.Flux1DSequence):
    """Baseflow [mm/T]."""


class ActualRecharge(sequencetools.FluxSequence):
    """Actual recharge [mm/T]."""

    NDIM, NUMERIC = 0, False


class DelayedRecharge(sequencetools.FluxSequence):
    """Delayed recharge [mm/T]."""

    NDIM, NUMERIC = 0, False
