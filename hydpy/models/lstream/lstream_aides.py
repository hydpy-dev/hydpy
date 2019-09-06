# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
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
    CLASSES = (Temp,
               HMin,
               HMax,
               QMin,
               QMax,
               QTest)
