# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class L(sequencetools.ReceiverSequence):
    """Water level [m]."""

    NDIM, NUMERIC = 1, False
