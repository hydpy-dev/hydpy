# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class MoistureChange(sequencetools.LogSequence):
    """The (last) change in soil moisture of each bin [-].

    Some methods of |ga_garto| take the direction of the last moisture change as a
    marker for a bin's state:

    ToDo: Would constants like "INACTIVE" or "REDISTRIBUTION" simplify the methods?
    """

    NDIM, NUMERIC = 2, False
