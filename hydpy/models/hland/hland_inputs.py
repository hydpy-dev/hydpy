# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from ...framework import sequencetools


class P(sequencetools.InputSequence):
    """Precipitation [mm]."""
    NDIM, NUMERIC = 0, False

class T(sequencetools.InputSequence):
    """Temperature [°C]."""
    NDIM, NUMERIC = 0, False

class TN(sequencetools.InputSequence):
    """Normal temperature [°C]."""
    NDIM, NUMERIC = 0, False

class EPN(sequencetools.InputSequence):
    """Normal potential evaporation [mm]."""
    NDIM, NUMERIC = 0, False

class InputSequences(sequencetools.InputSequences):
    """Input sequences of the hland model."""
    _SEQCLASSES = (P, T, TN, EPN)
