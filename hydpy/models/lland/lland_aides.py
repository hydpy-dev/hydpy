# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class SfA(sequencetools.AideSequence):
    """Sättigungsflächen-Aktivität (activity of the saturated surface) [mm]."""
    NDIM, NUMERIC = 1, False


class Exz(sequencetools.AideSequence):
    """Bodenfeuchteüberschuss (excess of soil water) [mm]."""
    NDIM, NUMERIC = 1, False


class BVl(sequencetools.AideSequence):
    """Berechneter Bodenwasserverlust (calculated amount of water that should
    be released from the soil) [mm]."""
    NDIM, NUMERIC = 1, False


class MVl(sequencetools.AideSequence):
    """Möglicher Bodenwasserverlust (maximum amount of water released that can
    be released from the soil) [mm]."""
    NDIM, NUMERIC = 1, False


class RVl(sequencetools.AideSequence):
    """Relation von MVl und BVl (ratio of MVl and BVl) [-]."""
    NDIM, NUMERIC = 1, False


class EPW(sequencetools.AideSequence):
    """Potenzielle Evaporation/Evapotranspiration von Wasserflächen (potential
    evaporation/evapotranspiration combined from all water areas) [mm]."""
    NDIM, NUMERIC = 0, False


class AideSequences(sequencetools.AideSequences):
    """Aide sequences of the HydPy-L-Land model."""
    _SEQCLASSES = (SfA,
                   Exz,
                   BVl,
                   MVl,
                   RVl,
                   EPW)
