# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Alertness(sequencetools.FactorSequence):
    """The current need for low water control [-]."""

    NDIM, NUMERIC = 0, False
