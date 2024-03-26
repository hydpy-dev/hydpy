# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class LongQ(sequencetools.OutletSequence):
    """The longitudinal outflow of the last channel segment [m³/s]."""

    NDIM, NUMERIC = 1, False
