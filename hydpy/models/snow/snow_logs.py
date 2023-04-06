# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
import warnings


# ...from HydPy
from hydpy.core import sequencetools


class GLocalMax(sequencetools.LogSequence):
    """Local melt threshold [mm]."""

    NDIM, NUMERIC = 1, False
