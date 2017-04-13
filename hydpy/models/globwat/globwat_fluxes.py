# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools

class ERain(sequencetools.Sequence):
    """rainfed evaporation [mm/day]"""
    NDIM, NUMERIC = 1, False
    
class EIncrirr(sequencetools.Sequence):
    """incremental evaporation due to irrigation [mm/day]"""
    NDIM, NUMERIC = 1, False
    
class EC(sequencetools.Sequence):
    """crop evaporation under irrigation [mm/day]"""
    NDIM, NUMERIC = 1, False

class R0(sequencetools.Sequence):
    """(sub-)surface runoff [mm/day]"""
    NDIM, NUMERIC = 1, False

class FluxSequences(sequencetools.SubSequences):
    """Flux sequences of the hland model."""
    _SEQCLASSES = (ERain, EIncrirr, EC, R0)