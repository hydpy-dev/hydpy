# pylint: disable=missing-module-docstring
from tkinter.constants import NUMERIC

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Index(sequencetools.AideSequence):
    """? [-]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class Excess(sequencetools.AideSequence):
    """? [-]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class Weight(sequencetools.AideSequence):
    """? [-]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, 1.0)
