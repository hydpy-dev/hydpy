# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Temp(sequencetools.AideSequence):
    """Temporäre Variable (temporary variable) [-]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AideSequences(sequencetools.AideSequences):
    """Aide sequences of HydPy-L-Stream."""
    _SEQCLASSES = (Temp,)