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

#class EIncrirr(sequencetools.Sequence):
#    """incremental evaporation due to irrigation [mm/day]"""
#    NDIM, NUMERIC = 1, False

class EC(sequencetools.Sequence):
    """crop evaporation under irrigation [mm/day]"""
    NDIM, NUMERIC = 1, False

class EOW(sequencetools.Sequence):
    """evaporation over open water [mm/day]."""
    NDIM, NUMERIC = 1, False

class EGrid(sequencetools.Sequence):
    """sum of all evaporation per grid cell [mm/day]"""
    NDIM, NUMERIC = 1, False

class RO(sequencetools.Sequence):
    """vertical (sub-)surface runoff [mm/day]"""
    NDIM, NUMERIC = 1, False

#class ROH(sequencetools.Sequence):
#    """horizontal (sub-)surface runoff [mm/day]"""
#    NDIM, NUMERIC = 1, False

class EIncrOW(sequencetools.Sequence):
    """incremental evaporation over open water [mm/day]"""
    NDIM, NUMERIC = 1, False

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the hland model."""
    _SEQCLASSES = (ERain, EC, RO, EOW, EIncrOW, EGrid)