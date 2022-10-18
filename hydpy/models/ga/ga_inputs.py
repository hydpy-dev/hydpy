# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Rainfall(sequencetools.InputSequence):
    """Rainfall [mm/T]."""

    NDIM, NUMERIC = 0, False


class CapillaryRise(sequencetools.InputSequence):
    """Capillary rise [mm/T]."""

    NDIM, NUMERIC = 0, False


class Evaporation(sequencetools.InputSequence):
    """Evaporation [mm/T]."""

    NDIM, NUMERIC = 0, False
