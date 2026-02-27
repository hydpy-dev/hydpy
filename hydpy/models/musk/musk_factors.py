# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.models.musk import musk_sequences


class ReferenceWaterDepth(musk_sequences.FactorSequence1D):
    """Reference water depth [m]."""

    SPAN = (0.0, None)


class WettedArea(musk_sequences.FactorSequence1D):
    """Wetted area [m²]."""

    SPAN = (0.0, None)


class SurfaceWidth(musk_sequences.FactorSequence1D):
    """Surface width [m]."""

    SPAN = (0.0, None)


class Celerity(musk_sequences.FactorSequence1D):
    """Kinematic celerity (wave speed) [m/T]."""


class CorrectingFactor(musk_sequences.FactorSequence1D):
    """Correcting factor [-]."""

    SPAN = (0.0, None)


class Coefficient1(musk_sequences.FactorSequence1D):
    """First coefficient of the Muskingum working formula [-]."""


class Coefficient2(musk_sequences.FactorSequence1D):
    """Second coefficient of the Muskingum working formula [-]."""


class Coefficient3(musk_sequences.FactorSequence1D):
    """Third coefficient of the Muskingum working formula [-]."""
