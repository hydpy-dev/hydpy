# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *

# ...from wq
from hydpy.models.wq import wq_variables


class Discharges(wq_variables.MixinTrapezesOrSectors, sequencetools.FluxSequence):
    """The discharge of each trapeze range [m³/s]."""

    SPAN = (None, None)


class Discharge(sequencetools.FluxSequence):
    """Total discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (None, None)
