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
    """surface runoff [mm/day]"""
    NDIM, NUMERIC = 1, False

class ROH(sequencetools.FluxSequence):
    """horizontal (sub-)surface runoff [mm/day]"""
    NDIM, NUMERIC = 1, False

class ROV(sequencetools.FluxSequence):
    """vertical (sub-)surface runoff [mm/day]"""
    NDIM, NUMERIC = 1, False

class ESub(sequencetools.FluxSequence):
    """sum of all evaporation per subbasin [mm/day]"""
    NDIM, NUMERIC = 0, False

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the globwat model."""
    _SEQCLASSES = (ERain, EC, EOW, EGrid, RO, ROH, ROV, ESub)