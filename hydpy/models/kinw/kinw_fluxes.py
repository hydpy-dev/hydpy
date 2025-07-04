# pylint: disable=missing-module-docstring

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


class Inflow(sequencetools.FluxSequence):
    """Flow into the first channel segment [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class QG(sequencetools.FluxSequence):
    """Durchfluss gesamt (total discharge) [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class InternalFlow(sequencetools.FluxSequence):
    """Flow between the channel segments [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)

    __HYDPY__DELTA_SEGMENTS__ = -1


class QA(sequencetools.FluxSequence):
    """Abfluss aus Gerinnestrecke (outflow out of the channel) [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class Outflow(sequencetools.FluxSequence):
    """Flow out of the last channel segment [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class DH(sequencetools.FluxSequence):
    """Wasserstandänderung (temporal change of the water stage) [m/s]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)
