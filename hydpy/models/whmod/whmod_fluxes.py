# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class NiederschlagRichter(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 0, False


class InterzeptionsVerdunstung(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class NiedNachInterz(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class ZuflussBoden(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class Oberflaechenabfluss(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class RelBodenfeuchte(sequencetools.FluxSequence):
    """[-]"""
    NDIM, NUMERIC = 1, False


class Sickerwasser(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class Saettigungsdampfdruckdefizit(sequencetools.FluxSequence):
    """[mbar]"""
    NDIM, NUMERIC = 0, False


class MaxVerdunstung(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class AktVerdunstung(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class PotKapilAufstieg(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class KapilAufstieg(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class AktGrundwasserneubildung(sequencetools.FluxSequence):
    """[mm]"""
    NDIM, NUMERIC = 1, False


class FluxSequences(sequencetools.FluxSequences):
    CLASSES = (NiederschlagRichter,
               InterzeptionsVerdunstung,
               NiedNachInterz,
               ZuflussBoden,
               Oberflaechenabfluss,
               RelBodenfeuchte,
               Sickerwasser,
               Saettigungsdampfdruckdefizit,
               MaxVerdunstung,
               AktVerdunstung,
               PotKapilAufstieg,
               KapilAufstieg,
               AktGrundwasserneubildung)
