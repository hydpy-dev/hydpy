# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod.whmod_sequences import Flux1DSequence


class NiederschlagRichter(sequencetools.FluxSequence):
    """[mm]"""

    NDIM, NUMERIC = 0, False


class InterzeptionsVerdunstung(Flux1DSequence):
    """[mm]"""


class NiedNachInterz(Flux1DSequence):
    """[mm]"""


class Seeniederschlag(Flux1DSequence):
    """[mm]"""


class ZuflussBoden(Flux1DSequence):
    """[mm]"""


class Oberflaechenabfluss(Flux1DSequence):
    """[mm]"""


class Sickerwasser(Flux1DSequence):
    """[mm]"""


class MaxVerdunstung(Flux1DSequence):
    """[mm]"""


class Bodenverdunstung(Flux1DSequence):
    """[mm]"""


class Seeverdunstung(Flux1DSequence):
    """[mm]"""


class AktVerdunstung(Flux1DSequence):
    """[mm]"""


class PotKapilAufstieg(Flux1DSequence):
    """[mm]"""


class KapilAufstieg(Flux1DSequence):
    """[mm]"""


class PotGrundwasserneubildung(Flux1DSequence):
    """[mm]"""


class Basisabfluss(Flux1DSequence):
    """[mm]"""


class AktGrundwasserneubildung(sequencetools.FluxSequence):
    """[mm]"""

    NDIM, NUMERIC = 0, False


class VerzGrundwasserneubildung(sequencetools.FluxSequence):
    """[mm]"""

    NDIM, NUMERIC = 0, False
