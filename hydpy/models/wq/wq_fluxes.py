# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from wq
from hydpy.models.wq import wq_variables


class Discharges(wq_variables.MixinTrapezesOrSectors, sequencetools.FluxSequence):
    """The discharge of each trapeze range [m³/s]."""

    NUMERIC, SPAN = False, (None, None)


class Discharge(sequencetools.FluxSequence):
    """Total discharge [m³/s]."""

    NDIM = 0
    NUMERIC = False
    SPAN = (None, None)
