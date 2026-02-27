# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class DHS(sequencetools.FactorSequence):
    """External change of the surface water depth [mm/T]."""

    NDIM = 0
    NUMERIC = False
    SPAN = (None, None)
