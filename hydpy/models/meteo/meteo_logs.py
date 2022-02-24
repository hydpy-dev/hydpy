# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedSunshineDuration(sequencetools.LogSequence):
    """Logged sunshine duration [h]."""

    NDIM, NUMERIC = 1, False


class LoggedUnadjustedGlobalRadiation(sequencetools.LogSequence):
    """Logged unadjusted global radiation [ToDo]."""

    NDIM, NUMERIC = 1, False
