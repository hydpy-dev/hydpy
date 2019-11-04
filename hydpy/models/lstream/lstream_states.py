# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class QZ(sequencetools.StateSequence):
    """Zufluss in Gerinnestrecke (inflow into the channel) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class QA(sequencetools.StateSequence):
    """Abfluss aus Gerinnestrecke (outflow out of the channel) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)
