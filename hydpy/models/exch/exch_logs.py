# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedWaterLevel(sequencetools.LogSequenceFixed):
    """Logged water level [m]."""

    NUMERIC = False
    SHAPE = 2
