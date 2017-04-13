# -*- coding: utf-8 -*-
"""Author: Wuestenfeld
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """Precipitation [mm/d]."""
    NDIM, NUMERIC = 0, False

class E0(sequencetools.InputSequence):
    """reference evaporation [mm/d]."""
    NDIM, NUMERIC = 0, False

#class T(sequencetools.InputSequence):
#    """Temperature [°C]."""
#    NDIM, NUMERIC = 0, False

class InputSequences(sequencetools.SubSequences):
    """Input sequences of the globwat model."""
    SEQCLASSES = (P, E0)
