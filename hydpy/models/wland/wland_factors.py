# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class DHS(sequencetools.FactorSequence):
    """External change of the surface water depth [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
