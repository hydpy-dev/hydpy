# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Nied(sequencetools.InputSequence):
    """Niederschlag (precipitation) [mm]."""
    NDIM, NUMERIC = 0, False


class TemL(sequencetools.InputSequence):
    """Lufttemperatur (air temperature) [°C]."""
    NDIM, NUMERIC = 0, False


class Glob(sequencetools.InputSequence):
    """Globalstrahlung (global radiation) [W/m²]."""
    NDIM, NUMERIC = 0, False


class PET(sequencetools.InputSequence):
    """Potenzielle Verdunstung (potential evapotranspiration) [mm]."""
    NDIM, NUMERIC = 0, False


class InputSequences(sequencetools.InputSequences):
    """Input sequences of the HydPy-L-Land model."""
    _SEQCLASSES = (Nied,
                   TemL,
                   Glob,
                   PET)
