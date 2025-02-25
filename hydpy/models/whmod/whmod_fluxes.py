# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod import whmod_sequences


class NiederschlagRichter(sequencetools.FluxSequence):
    """[mm/T]"""

    NDIM, NUMERIC = 0, False


class InterzeptionsVerdunstung(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class NiedNachInterz(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Seeniederschlag(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class ZuflussBoden(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Oberflaechenabfluss(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Sickerwasser(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class MaxVerdunstung(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Bodenverdunstung(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Seeverdunstung(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class AktVerdunstung(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class PotKapilAufstieg(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class KapilAufstieg(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class PotGrundwasserneubildung(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class Basisabfluss(whmod_sequences.Flux1DSequence):
    """[mm/T]"""


class AktGrundwasserneubildung(sequencetools.FluxSequence):
    """[mm/T]"""

    NDIM, NUMERIC = 0, False


class VerzGrundwasserneubildung(sequencetools.FluxSequence):
    """[mm/T]"""

    NDIM, NUMERIC = 0, False
