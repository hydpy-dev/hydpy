# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class FR(sequencetools.AideSequence):
    """Fraction rainfall / total precipitation [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (0.0, 1.0)


class WE(sequencetools.AideSequence):
    """Wetness index in the elevated region [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (None, None)


class W(sequencetools.AideSequence):
    """Wetness index in the lowland region [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (None, None)


class BetaE(sequencetools.AideSequence):
    """Evapotranspiration reduction factor in the elevated region [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (None, None)


class Beta(sequencetools.AideSequence):
    """Evapotranspiration reduction factor in the lowland region [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (None, None)


class DVEq(sequencetools.AideSequence):
    """Equilibrium storage deficit of the vadose zone for the actual groundwater
    depth [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (None, None)


class DGEq(sequencetools.AideSequence):
    """Equilibrium groundwater depth for the actual storage deficit of the vadose
    zone [mm]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (None, None)


class GF(sequencetools.AideSequence):
    """Gain factor for changes in groundwater depth [-]."""

    NDIM: Final[Literal[0]] = 0
    NUMERIC = False
    SPAN = (None, None)
