# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LoggedTotalRemoteDischarge(sequencetools.LogSequence):
    """Logged discharge values from somewhere else [m³/s]."""

    NDIM, NUMERIC = 1, False


class LoggedOutflow(sequencetools.LogSequence):
    """Logged discharge values from the dam itself [m³/s]."""

    NDIM, NUMERIC = 1, False


class LoggedAdjustedEvaporation(sequencetools.LogSequenceFixed):
    """Logged adjusted evaporation [m³/s]."""

    NUMERIC = False
    SHAPE = 1


class LoggedRequiredRemoteRelease(sequencetools.LogSequenceFixed):
    """Logged required discharge values computed by another model [m³/s]."""

    NUMERIC = False
    SHAPE = 1


class LoggedAllowedRemoteRelief(sequencetools.LogSequenceFixed):
    """Logged allowed discharge values computed by another model [m³/s]."""

    NUMERIC = False
    SHAPE = 1


class LoggedOuterWaterLevel(sequencetools.LogSequenceFixed):
    """Logged water level directly below the dam [m]."""

    NUMERIC = False
    SHAPE = 1


class LoggedRemoteWaterLevel(sequencetools.LogSequenceFixed):
    """Logged water level at a remote location [m]."""

    NUMERIC = False
    SHAPE = 1
