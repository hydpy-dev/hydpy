# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *

from hydpy.models.hland import hland_masks
from hydpy.models.hland import hland_sequences


class TC(hland_sequences.Factor1DSequence):
    """Corrected temperature [°C]."""

    mask = hland_masks.Complete()


class FracRain(hland_sequences.Factor1DSequence):
    """Fraction rainfall / total precipitation [-]."""

    mask = hland_masks.Complete()


class Cov(hland_sequences.Factor1DSequence):
    """ToDo [-]."""

    mask = hland_masks.Complete()


class GAct(hland_sequences.Factor1DSequence):
    """Actual degree day factor for glacier ice [mm/°C/T]."""

    mask = hland_masks.Glacier()


class ContriArea(sequencetools.FactorSequence):
    """Fraction of the "soil area" contributing to runoff generation [-]."""

    NDIM: Final[Literal[0]] = 0
