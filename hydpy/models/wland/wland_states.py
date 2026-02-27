# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from wland
from hydpy.models.wland import wland_sequences


class IC(wland_sequences.StateSequence1DLand):
    """Interception storage [mm]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (None, None)


class SP(wland_sequences.StateSequence1DLand):
    """Snow pack [mm]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (None, None)


class DVE(sequencetools.StateSequence):
    """Storage deficit of the vadose zone in the elevated region [mm]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class DV(sequencetools.StateSequence):
    """Storage deficit of the vadose zone in the lowland region [mm]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class HGE(sequencetools.StateSequence):
    """Groundwater level in the elevated region [mm]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class DG(sequencetools.StateSequence):
    """Groundwater depth in the lowland region [mm]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class HQ(sequencetools.StateSequence):
    """Level of the quickflow reservoir [mm]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class HS(sequencetools.StateSequence):
    """Surface water level [mm]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)
