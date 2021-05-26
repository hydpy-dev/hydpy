# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm]."""

    NDIM, NUMERIC = 0, False


class Evaporation(sequencetools.InputSequence):
    """Potential evaporation [mm]."""

    NDIM, NUMERIC = 0, False
