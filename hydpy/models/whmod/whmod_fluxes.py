# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod import whmod_sequences


class NiederschlagRichter(sequencetools.FluxSequence):
    """[mm]"""

    NDIM, NUMERIC = 0, False


class InterzeptionsVerdunstung(whmod_sequences.Flux1DSequence):
    """[mm]"""


class NiedNachInterz(whmod_sequences.Flux1DSequence):
    """[mm]"""


class Seeniederschlag(whmod_sequences.Flux1DSequence):
    """[mm]"""


class ZuflussBoden(whmod_sequences.Flux1DSequence):
    """[mm]"""


class Oberflaechenabfluss(whmod_sequences.Flux1DSequence):
    """[mm]"""


class Sickerwasser(whmod_sequences.Flux1DSequence):
    """[mm]"""


class MaxVerdunstung(whmod_sequences.Flux1DSequence):
    """[mm]"""


class Bodenverdunstung(whmod_sequences.Flux1DSequence):
    """[mm]"""


class Seeverdunstung(whmod_sequences.Flux1DSequence):
    """[mm]"""


class AktVerdunstung(whmod_sequences.Flux1DSequence):
    """[mm]"""


class PotKapilAufstieg(whmod_sequences.Flux1DSequence):
    """[mm]"""


class KapilAufstieg(whmod_sequences.Flux1DSequence):
    """[mm]"""


class PotGrundwasserneubildung(whmod_sequences.Flux1DSequence):
    """[mm]"""


class Basisabfluss(whmod_sequences.Flux1DSequence):
    """[mm]"""


class AktGrundwasserneubildung(sequencetools.FluxSequence):
    """[mm]"""

    NDIM, NUMERIC = 0, False


class VerzGrundwasserneubildung(sequencetools.FluxSequence):
    """[mm]"""

    NDIM, NUMERIC = 0, False
