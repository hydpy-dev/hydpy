# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Abfluss (runoff) [m³/s]."""
    NDIM, NUMERIC = 0, False


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-L-Lake."""
    _SEQCLASSES = (Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-L-Lake."""
    _SEQCLASSES = (Q,)