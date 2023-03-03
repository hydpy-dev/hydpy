# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """Precipitation [mm]."""

    NDIM, NUMERIC = 0, False


class T(sequencetools.InputSequence):
    """Temperature [°C]."""

    NDIM, NUMERIC = 0, False
