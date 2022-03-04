# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.ReceiverSequence):
    """Remote discharge [m³/s]."""

    NDIM, NUMERIC = 0, False


class D(sequencetools.ReceiverSequence):
    """Water demand [m³/s]."""

    NDIM, NUMERIC = 0, False


class S(sequencetools.ReceiverSequence):
    """Required water supply [m³/s]."""

    NDIM, NUMERIC = 0, False


class R(sequencetools.ReceiverSequence):
    """Allowed water relief [m³/s]."""

    NDIM, NUMERIC = 0, False
