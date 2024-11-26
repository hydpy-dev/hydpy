# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from wland
from hydpy.models.wland import wland_sequences


class IC(wland_sequences.StateSequence1DLand):
    """Interception storage [mm]."""

    NDIM, NUMERIC, SPAN = 1, True, (None, None)


class SP(wland_sequences.StateSequence1DLand):
    """Snow pack [mm]."""

    NDIM, NUMERIC, SPAN = 1, True, (None, None)


class DVE(sequencetools.StateSequence):
    """Storage deficit of the vadose zone in the elevated region [mm]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class DV(sequencetools.StateSequence):
    """Storage deficit of the vadose zone in the lowland region [mm]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class HGE(sequencetools.StateSequence):
    """Groundwater level in the elevated region [mm]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class DG(sequencetools.StateSequence):
    """Groundwater depth in the lowland region [mm]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class HQ(sequencetools.StateSequence):
    """Level of the quickflow reservoir [mm]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class HS(sequencetools.StateSequence):
    """Surface water level [mm]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)
