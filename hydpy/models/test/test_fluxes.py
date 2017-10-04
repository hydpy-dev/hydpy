# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.FluxSequence):
    """Storage loss [mm/T]"""
    NDIM, NUMERIC, SPAN = 0, True, (0., None)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the Test model."""
    _SEQCLASSES = (Q,)
