# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.ReceiverSequence):
    """Discharge [m³/s]."""
    NDIM, NUMERIC = 0, False


class D(sequencetools.ReceiverSequence):
    """Water demand [m³/s]."""
    NDIM, NUMERIC = 0, False


class S(sequencetools.ReceiverSequence):
    """Water supply [m³/s]."""
    NDIM, NUMERIC = 0, False


class R(sequencetools.ReceiverSequence):
    """Water relief [m³/s]."""
    NDIM, NUMERIC = 0, False
