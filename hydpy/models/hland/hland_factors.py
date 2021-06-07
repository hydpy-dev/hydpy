# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from hland
from hydpy.models.hland import hland_masks
from hydpy.models.hland import hland_sequences


class TMean(sequencetools.FactorSequence):
    """Mean subbasin temperature [°C]."""

    NDIM = 0


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


class ContriArea(sequencetools.FactorSequence):
    """Fraction of the "soil area" contributing to runoff generation [-]."""

    NDIM = 0
