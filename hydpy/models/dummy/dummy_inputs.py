# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class InterceptedWater(sequencetools.InputSequence):
    """Intercepted water [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class SoilWater(sequencetools.InputSequence):
    """Soil water content [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class SnowCover(sequencetools.InputSequence):
    """Snow cover degree [-]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class SnowyCanopy(sequencetools.InputSequence):
    """Snow cover degree in the canopies of tree-like vegetation (is |numpy.nan| for
    non-tree-like vegetation) [-]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class SnowAlbedo(sequencetools.InputSequence):
    """Snow albedo [-]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, 1.0)
