# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools

class ERain(sequencetools.FluxSequence):
    """rainfed evaporation [mm/day]"""
    NDIM, NUMERIC = 1, False

#class EIncrirr(sequencetools.FluxSequence):
#    """incremental evaporation due to irrigation [mm/day]"""
#    NDIM, NUMERIC = 1, False

class EC(sequencetools.FluxSequence):
    """crop evaporation under irrigation [mm/day]"""
    NDIM, NUMERIC = 1, False

class EOW(sequencetools.FluxSequence):
    """evaporation over open water [mm/day]."""
    NDIM, NUMERIC = 1, False

class EGrid(sequencetools.FluxSequence):
    """sum of all evaporation per grid cell [mm/day]"""
    NDIM, NUMERIC = 1, False

class RO(sequencetools.FluxSequence):
    """vertical (sub-)surface runoff [mm/day]"""
    NDIM, NUMERIC = 1, False

#class ROH(sequencetools.FluxSequence):
#    """horizontal (sub-)surface runoff [mm/day]"""
#    NDIM, NUMERIC = 1, False

class EIncrOW(sequencetools.FluxSequence):
    """incremental evaporation over open water [mm/day]"""
    NDIM, NUMERIC = 1, False

#class Q(sequencetools.FluxSequence):
#    """runoff at the subbasin outlet [mm]."""
#    NDIM, NUMERIC = 0, False

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the hland model."""
    _SEQCLASSES = (ERain, EC, RO, EOW, EIncrOW, EGrid)