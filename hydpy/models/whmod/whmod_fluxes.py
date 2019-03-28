# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Sequence1D(sequencetools.FluxSequence):
    NDIM, NUMERIC = 1, False

    @property
    def refweights(self):
        return self.subseqs.seqs.model.parameters.derived.relarea


class NiederschlagRichter(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 0, False


class InterzeptionsVerdunstung(Sequence1D):
    """[mm]"""


class NiedNachInterz(Sequence1D):
    """[mm]"""


class Seeniederschlag(Sequence1D):
    """[mm]"""


class ZuflussBoden(Sequence1D):
    """[mm]"""


class Oberflaechenabfluss(Sequence1D):
    """[mm]"""


class RelBodenfeuchte(Sequence1D):
    """[-]"""


class Sickerwasser(Sequence1D):
    """[mm]"""


class Saettigungsdampfdruckdefizit(sequencetools.FluxSequence):
    """[mbar]"""
    NDIM, NUMERIC = 0, False


class MaxVerdunstung(Sequence1D):
    """[mm]"""


class Bodenverdunstung(Sequence1D):
    """[mm]"""


class Seeverdunstung(Sequence1D):
    """[mm]"""


class AktVerdunstung(Sequence1D):
    """[mm]"""


class PotKapilAufstieg(Sequence1D):
    """[mm]"""


class KapilAufstieg(Sequence1D):
    """[mm]"""


class AktGrundwasserneubildung(Sequence1D):
    """[mm]"""


class FluxSequences(sequencetools.FluxSequences):
    CLASSES = (NiederschlagRichter,
               InterzeptionsVerdunstung,
               NiedNachInterz,
               Seeniederschlag,
               ZuflussBoden,
               Oberflaechenabfluss,
               RelBodenfeuchte,
               Sickerwasser,
               Saettigungsdampfdruckdefizit,
               MaxVerdunstung,
               Bodenverdunstung,
               Seeverdunstung,
               AktVerdunstung,
               PotKapilAufstieg,
               KapilAufstieg,
               AktGrundwasserneubildung)
