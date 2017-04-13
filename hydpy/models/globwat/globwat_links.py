# -*- coding: utf-8 -*-
"""Author: Christoph Tyralla
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.Sequence):
    """Runoff [m³/s]."""
    NDIM, NUMERIC = 0, False

class DownstreamSequences(sequencetools.SubSequences):
    """Downstream link sequences of the hland model."""
    SEQCLASSES = (Q,)
