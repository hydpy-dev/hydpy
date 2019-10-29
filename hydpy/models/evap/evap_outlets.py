# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class E(sequencetools.OutletSequence):
    """(Potential) Evapo(trans)piration [mm/T]."""
    NDIM, NUMERIC = 0, False
