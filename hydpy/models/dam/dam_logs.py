# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class LoggedTotalRemoteDischarge(sequencetools.LogSequence):
    """Discharge values received from cross sections far downstream [m3/s]."""
    NDIM, NUMERIC = 1, False


class LoggedOutflow(sequencetools.LogSequence):
    """Discharge values received from cross sections far downstream [m3/s]."""
    NDIM, NUMERIC = 1, False


class LogSequences(sequencetools.LogSequences):
    """Log sequences of the dam model."""
    _SEQCLASSES = (LoggedTotalRemoteDischarge,
                   LoggedOutflow)
