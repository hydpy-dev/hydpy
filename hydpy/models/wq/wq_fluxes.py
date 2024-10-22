# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Discharges(sequencetools.FluxSequence):
    """The discharge of each trapeze range [m³/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)


class Discharge(sequencetools.FluxSequence):
    """Total discharge [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
