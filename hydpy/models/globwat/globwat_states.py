# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class R(sequencetools.StateSequence):
    """groundwater recharge [mm/d]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class S(sequencetools.StateSequence):
    """available soil moisture on t [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class B(sequencetools.StateSequence):
    """water balance on t [mm]."""
    NDIM, NUMERIC, SPAN  = 1, False, (None, None)

class BOW(sequencetools.StateSequence):
    """open water balance on t [mm]."""
    NDIM, NUMERIC, SPAN  = 1, False, (None, None)

class Bsb(sequencetools.StateSequence):
    """(sub-)basin balance [m³/month]."""
    NDIM, NUMERIC, SPAN  = 0, False, (None, None)

class Ssb(sequencetools.StateSequence):
    """(sub-)basin storage [m³]."""
    NDIM, NUMERIC, SPAN  = 0, False, (0., None)

class Qout(sequencetools.StateSequence):
    """outflow [m³/month]."""
    NDIM, NUMERIC, SPAN  = 0, False, (0., None)

class Qin(sequencetools.StateSequence):
    """inflow [m³/month]."""
    NDIM, NUMERIC, SPAN  = 0, False, (0., None)

class StateSequences(sequencetools.StateSequences):
    """State sequences of the globwat model."""
    _SEQCLASSES = (R, S, B, BOW, Bsb, Ssb, Qout, Qin)