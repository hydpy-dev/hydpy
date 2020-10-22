# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.InletSequence):
    """Discharge [m³/s]."""

    NDIM, NUMERIC = 0, False


class S(sequencetools.InletSequence):
    """Water supply [m³/s]."""

    NDIM, NUMERIC = 0, False


class R(sequencetools.InletSequence):
    """Water relief [m³/s]."""

    NDIM, NUMERIC = 0, False
