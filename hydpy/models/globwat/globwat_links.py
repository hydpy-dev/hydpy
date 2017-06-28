# -*- coding: utf-8 -*-
"""Author: Wuestenfeld
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Runoff [m³/s]."""
    NDIM, NUMERIC = 1, False

class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the GlobWat model."""
    _SEQCLASSES = (Q,)

class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of the GlobWat model."""
    _SEQCLASSES = (Q,)
