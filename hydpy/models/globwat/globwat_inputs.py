# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """precipitation [mm/d]."""
    NDIM, NUMERIC = 1, False

class E0(sequencetools.InputSequence):
    """reference evaporation [mm/d]."""
    NDIM, NUMERIC = 1, False

class InputSequences(sequencetools.InputSequences):
    """Input sequences of the globwat model."""
    _SEQCLASSES = (P, E0)
