# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class R(sequencetools.StateSequence):
    """groundwater recharge [mm/d]"""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)
     
class S(sequencetools.StateSequence):
    """changes in storage on t [mm]"""    
    NDIM, NUMERIC, SPAN = 1, False, (0., None)
    
class B(sequencetools.StateSequence):
    """water balance on t [mm]"""
    NDIM, NUMERIC, SPAN  = 1, False, (None, None)

class StateSequences(sequencetools.StateSequences):
    """State sequences of the globwat model."""
    _SEQCLASSES = (R, S, B)

