# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Discharge at a crosssection far downstream [m³/s]."""
    NDIM, NUMERIC = 0, False


class ReceiverSequences(sequencetools.LinkSequences):
    """Information link sequences of the dam model."""
    _SEQCLASSES = (Q,)
