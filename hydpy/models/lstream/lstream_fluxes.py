# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class QZ(sequencetools.FluxSequence):
    """Mittlerer Zufluss in Gerinnestrecke (average inflow into the channel)
    [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class QZA(sequencetools.FluxSequence):
    """Aktueller Zufluss in Gerinnestrecke (current inflow into the channel)
    [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class QG(sequencetools.FluxSequence):
    """Durchfluss gesamt (total discharge) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class QA(sequencetools.FluxSequence):
    """Abfluss aus Gerinnestrecke (outflow out of the channel) [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class DH(sequencetools.FluxSequence):
    """Wasserstandänderung (temporal change of the water stage) [m/s]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)
