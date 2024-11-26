# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from hland
from hydpy.models.hland import hland_masks
from hydpy.models.hland import hland_sequences


class TC(hland_sequences.Factor1DSequence):
    """Corrected temperature [°C]."""

    mask = hland_masks.Complete()


class FracRain(hland_sequences.Factor1DSequence):
    """Fraction rainfall / total precipitation [-]."""

    mask = hland_masks.Complete()


class RfC(hland_sequences.Factor1DSequence):
    """Actual precipitation correction related to liquid precipitation [-]."""

    mask = hland_masks.Complete()


class SfC(hland_sequences.Factor1DSequence):
    """Actual precipitation correction related to frozen precipitation [-]."""

    mask = hland_masks.Complete()


class CFAct(hland_sequences.Factor1DSequence):
    """Actual degree day factor for snow (on glaciers or not) [mm/°C/T]."""

    mask = hland_masks.Land()


class SWE(hland_sequences.Factor2DSequence):
    """Snow water equivalent [mm]."""

    mask = hland_masks.Land()


class GAct(hland_sequences.Factor1DSequence):
    """Actual degree day factor for glacier ice [mm/°C/T]."""

    mask = hland_masks.Glacier()


class ContriArea(sequencetools.FactorSequence):
    """Fraction of the "soil area" contributing to runoff generation [-]."""

    NDIM = 0
