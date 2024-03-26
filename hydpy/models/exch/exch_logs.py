# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedWaterLevels(sequencetools.LogSequenceFixed):
    """Logged water levels [m]."""

    NUMERIC = False
    SHAPE = 2
