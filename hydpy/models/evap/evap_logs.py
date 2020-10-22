# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedGlobalRadiation(sequencetools.LogSequence):
    """Logged global radiation [MJ/m²/T]."""
    NDIM, NUMERIC = 1, False


class LoggedClearSkySolarRadiation(sequencetools.LogSequence):
    """Logged clear sky radiation [MJ/m²/T]."""
    NDIM, NUMERIC = 1, False
