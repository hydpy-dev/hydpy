# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class G(sequencetools.StateSequence):
    """Snow pack [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0, None)


class ETG(sequencetools.StateSequence):
    """Thermal state of Snow pack [°C]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, 0)


class GRatio(sequencetools.StateSequence):
    """Snow covered area [-]."""

    NDIM, NUMERIC, SPAN = 1, False, (0, 1)
    INIT = 0
