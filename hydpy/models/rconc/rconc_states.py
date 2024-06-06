# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SC(sequencetools.StateSequence):
    """Storage cascade for runoff concentration [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
