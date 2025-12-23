# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SPE(sequencetools.AideSequence):
    """Subbasin-internal redistribution excess of the snow's ice content [mm/T]."""

    NDIM = 1
    NUMERIC = False


class WCE(sequencetools.AideSequence):
    """Subbasin-internal redistribution excess of the snow's water content [mm/T]."""

    NDIM = 1
    NUMERIC = False
