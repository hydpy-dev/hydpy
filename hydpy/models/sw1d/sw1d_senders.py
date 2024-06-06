# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.SenderSequence):
    """The water level within the first channel segment [m]."""

    NDIM, NUMERIC = 1, False
