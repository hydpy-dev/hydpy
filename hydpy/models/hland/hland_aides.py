# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from ...framework import sequencetools

class Perc(sequencetools.AideSequence):
    """Percolation from the upper to the lower zone layer [mm]."""
    NDIM, NUMERIC = 0, False

class Q0(sequencetools.AideSequence):
    """Outflow from the upper zone layer [mm]."""
    NDIM, NUMERIC = 0, False

class AideSequences(sequencetools.AideSequences):
    """Aide sequences of the hland model."""
    _SEQCLASSES = (Perc, Q0)
