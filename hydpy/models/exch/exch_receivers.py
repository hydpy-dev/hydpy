# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.ReceiverSequence):
    """The water level at a single remote location [m]."""

    NDIM, NUMERIC = 0, False


class WaterLevels(sequencetools.ReceiverSequence):
    """The water level at multiple remote locations [m]."""

    NDIM, NUMERIC = 1, False
