# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevels(sequencetools.ReceiverSequence):
    """The water level at multiple remote locations [m]."""

    NDIM, NUMERIC = 1, False
