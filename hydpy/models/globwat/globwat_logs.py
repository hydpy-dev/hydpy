# -*- coding: utf-8 -*-
"""Author: Christoph Tyralla
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class QUH(sequencetools.Sequence):
    """Whole outflow delayed by means of the unit hydrograph [mm]."""
    NDIM, NUMERIC = 1, False

class LogSequences(sequencetools.SubSequences):
    """Log sequences of the hland model."""
    SEQCLASSES = (QUH,)
