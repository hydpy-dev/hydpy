# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class T(sequencetools.InputSequence):
    """Air temperature [°C]."""

    NDIM, NUMERIC = 0, False


class P(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM, NUMERIC = 0, False


class PET(sequencetools.InputSequence):
    """Potential evapotranspiration [mm/T]."""

    NDIM, NUMERIC = 0, False


class FXG(sequencetools.InputSequence):
    """Seepage/extraction (normalised to |AT|) [mm/T]."""

    NDIM, NUMERIC = 0, True


class FXS(sequencetools.InputSequence):
    """Surface water supply/extraction (normalised to |AT|) [mm/T]."""

    NDIM, NUMERIC = 0, False
