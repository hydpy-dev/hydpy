# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Inflow(sequencetools.FluxSequence):
    """Inflow [mm/T]."""

    NDIM = 0
    NUMERIC = False


class Outflow(sequencetools.FluxSequence):
    """Outflow [mm/T]."""

    NDIM = 0
    NUMERIC = False
