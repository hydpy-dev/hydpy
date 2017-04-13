# -*- coding: utf-8 -*-
"""Author: Christoph Tyralla
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools

class Perc(sequencetools.Sequence):
    """Percolation from the upper to the lower zone layer [mm]."""
    NDIM, NUMERIC = 0, False

class Q0(sequencetools.Sequence):
    """Outflow from the upper zone layer [mm]."""
    NDIM, NUMERIC = 0, False

class AideSequences(sequencetools.SubSequences):
    """Aide sequences of the hland model."""
    SEQCLASSES = (Perc, Q0)
