# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.OutletSequence):
    """Discharge [m³/s]."""
    NDIM, NUMERIC = 0, False


class S(sequencetools.OutletSequence):
    """Water supply [m³/s]."""
    NDIM, NUMERIC = 0, False


class R(sequencetools.OutletSequence):
    """Water relieve [m³/s]."""
    NDIM, NUMERIC = 0, False
