# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class L(sequencetools.ReceiverSequence):
    """Water level [m]."""

    NDIM, NUMERIC = 1, False
