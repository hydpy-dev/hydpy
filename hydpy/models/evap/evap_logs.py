# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedGlobalRadiation(sequencetools.LogSequence):
    """Logged global radiation [W/m²]."""

    NDIM, NUMERIC = 1, False


class LoggedClearSkySolarRadiation(sequencetools.LogSequence):
    """Logged clear sky radiation [W/m²]."""

    NDIM, NUMERIC = 1, False
