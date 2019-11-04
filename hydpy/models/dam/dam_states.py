# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterVolume(sequencetools.StateSequence):
    """Water volume [million m³]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)
