# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Branched(sequencetools.OutletSequence):
    """Branched outputs [e.g. m³/s]."""

    NDIM, NUMERIC = 1, False
