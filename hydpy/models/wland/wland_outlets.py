# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.OutletSequence):
    """Discharge [m³/s]."""

    NDIM, NUMERIC = 0, False
