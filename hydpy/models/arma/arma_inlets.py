# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Runoff [m³/s]."""
    NDIM, NUMERIC = 1, False


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the ARMA model."""
    _SEQCLASSES = (Q,)
