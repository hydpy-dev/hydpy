# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class V(sequencetools.StateSequence):
    """Wasservolumen (water volume) [m³]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class W(sequencetools.StateSequence):
    """Wasserstand (water stage) [m]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
