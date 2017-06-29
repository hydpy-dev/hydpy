# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Temp(sequencetools.AideSequence):
    """Temporäre Variable (temporary variable) [-]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class HMin(sequencetools.AideSequence):
    """Untere Wasserstandsgrenze (lower water stage boundary) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class HMax(sequencetools.AideSequence):
    """Obere Wasserstandsgrenze (upper water stage boundary) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class QMin(sequencetools.AideSequence):
    """Untere Abflussgrenze (lower discharge boundary) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class QMax(sequencetools.AideSequence):
    """Obere Abflussgrenze (upper discharge boundary) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class QTest(sequencetools.AideSequence):
    """Vergleichsabfluss (discharge to be compared) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class AideSequences(sequencetools.AideSequences):
    """Aide sequences of HydPy-L-Stream."""
    _SEQCLASSES = (Temp, HMin, HMax, QMin, QMax, QTest)
