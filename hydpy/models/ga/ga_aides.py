# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class InitialSurfaceWater(sequencetools.AideSequence):
    """The initial surface water depth at the beginning of a numerical substep [mm]."""

    NDIM, NUMERIC = 1, False


class ActualSurfaceWater(sequencetools.AideSequence):
    """The actual surface water depth [mm]."""

    NDIM, NUMERIC = 1, False
