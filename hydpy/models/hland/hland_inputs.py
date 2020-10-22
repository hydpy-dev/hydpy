# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """Precipitation [mm]."""
    NDIM, NUMERIC = 0, False


class T(sequencetools.InputSequence):
    """Temperature [°C]."""
    NDIM, NUMERIC = 0, False


class TN(sequencetools.InputSequence):
    """Normal temperature [°C]."""
    NDIM, NUMERIC = 0, False


class EPN(sequencetools.InputSequence):
    """Normal potential evaporation [mm]."""
    NDIM, NUMERIC = 0, False
