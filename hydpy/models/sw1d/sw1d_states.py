# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class WaterVolume(sequencetools.StateSequence):
    """Water volume [1000 m³].

    Note that the water volume stored in a channel segment might be slightly negative
    due to numerical inaccuracies (see ref:`sw1d_channel_internal_negative_volumes`) or
    even vastly negative due to erroneous data or configurations (see
    :ref:`sw1d_channel_excessive_water_withdrawal`).
    """

    NDIM: Final[Literal[0]] = 0
    SPAN = (None, None)


class Discharge(sequencetools.StateSequence):
    """Discharge [m³/s]."""

    NDIM: Final[Literal[0]] = 0
