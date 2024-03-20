# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Exchange(sequencetools.OutletSequence):
    """Bidirectional water exchange [m³/s]."""

    NDIM, NUMERIC = 1, False
