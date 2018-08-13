# -*- coding: utf-8 -*-

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LogIn(sequencetools.LogSequence):
    """The recent and the past inflow portions for the application of the
    different MA processes [m³/s]."""
    NDIM, NUMERIC, SPAN = 2, False, (None, None)


class LogOut(sequencetools.LogSequence):
    """The past outflow portions for the application of the
    different AR processes [m³/s]."""
    NDIM, NUMERIC, SPAN = 2, False, (None, None)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of the ARMA model."""
    CLASSES = (LogIn,
               LogOut)
