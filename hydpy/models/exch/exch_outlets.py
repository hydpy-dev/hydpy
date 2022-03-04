# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class E(sequencetools.OutletSequence):
    """Bidirectional water exchange [m³]."""

    NDIM, NUMERIC = 1, False
