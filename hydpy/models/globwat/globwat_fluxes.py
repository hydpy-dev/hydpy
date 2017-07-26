# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools

class ERain(sequencetools.FluxSequence):
    """rainfed evaporation [mm]"""
    NDIM, NUMERIC = 1, False

class EC(sequencetools.FluxSequence):
    """crop evaporation under irrigation [mm]"""
    NDIM, NUMERIC = 1, False

class EOW(sequencetools.FluxSequence):
    """evaporation over open water [mm]."""
    NDIM, NUMERIC = 1, False

class EGrid(sequencetools.FluxSequence):
    """sum of all evaporation per grid cell [mm]"""
    NDIM, NUMERIC = 1, False

class RO(sequencetools.FluxSequence):
    """surface runoff [mm]"""
    NDIM, NUMERIC = 1, False

class ROH(sequencetools.FluxSequence):
    """horizontal (sub-)surface runoff [mm]"""
    NDIM, NUMERIC = 1, False

class ROV(sequencetools.FluxSequence):
    """vertical (sub-)surface runoff [mm]"""
    NDIM, NUMERIC = 1, False

class ESub(sequencetools.FluxSequence):
    """sum of all evaporation per subbasin [mm]"""
    NDIM, NUMERIC = 0, False

class PSub(sequencetools.FluxSequence):
    """sum of all precipitation per subbasin [mm]"""
    NDIM, NUMERIC = 0, False

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the globwat model."""
    _SEQCLASSES = (ERain, EC, EOW, EGrid, RO, ROH, ROV, ESub, PSub)