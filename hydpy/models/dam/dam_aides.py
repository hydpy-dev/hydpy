# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterLevel(sequencetools.AideSequence):
    """Water level [m]."""
    NDIM, NUMERIC, SPAN = 0, True, (None, None)
