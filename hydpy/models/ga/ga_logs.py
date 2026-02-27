# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class MoistureChange(sequencetools.LogSequence):
    """The (last) change in soil moisture of each bin [-].

    Some methods of |ga_garto| take the direction of the last moisture change as a
    marker for a bin's state:

    ToDo: Would constants like "INACTIVE" or "REDISTRIBUTION" simplify the methods?
    """

    NDIM: Final[Literal[2]] = 2
    NUMERIC = False
