# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class T(sequencetools.InputSequence):
    """Air temperature [°C]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class P(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class FXG(sequencetools.InputSequence):
    """Seepage/extraction (normalised to |AT|) [mm/T]."""

    NDIM, NUMERIC = 0, True
    STANDARD_NAME = sequencetools.StandardInputNames.ARTIFICIAL_GROUNDWATER_RECHARGE


class FXS(sequencetools.InputSequence):
    """Surface water supply/extraction (normalised to |AT|) [mm/T]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.ARTIFICIAL_SURFACE_WATER_SUPPLY
