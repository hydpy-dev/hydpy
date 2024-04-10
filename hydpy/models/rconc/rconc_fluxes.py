# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Inflow(sequencetools.FluxSequence):
    """Input of the triangle unit hydrograph  [mm/T]."""

    NDIM = 0
    NUMERIC = False


class Outflow(sequencetools.FluxSequence):
    """Output of the triangle unit hydrograph  [mm/T]."""

    NDIM = 0
    NUMERIC = False
