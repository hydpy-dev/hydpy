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
    """[mm/T]"""


class SurfaceRunoff(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Percolation(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class SoilEvapotranspiration(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class LakeEvaporation(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class TotalEvapotranspiration(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class CapillaryRise(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class PotentialRecharge(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Baseflow(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class ActualRecharge(sequencetools.FluxSequence):
    """[mm/T]"""

    NDIM, NUMERIC = 0, False


class DelayedRecharge(sequencetools.FluxSequence):
    """[mm/T]"""

    NDIM, NUMERIC = 0, False
