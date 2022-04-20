# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.musk import musk_sequences


class Inflow(sequencetools.FluxSequence):
    """Inflow [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class ReferenceDischarge(musk_sequences.FluxSequence1D):
    """Reference discharge [m³/s]."""

    SPAN = (0.0, None)


class Outflow(sequencetools.FluxSequence):
    """Outflow [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
