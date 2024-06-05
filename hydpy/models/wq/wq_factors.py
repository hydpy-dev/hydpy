# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class WaterDepth(sequencetools.FactorSequence):
    """Water depth [m]."""

    NDIM, SPAN = 0, (0.0, None)


class WaterLevel(sequencetools.FactorSequence):
    """Water level [m]."""

    NDIM, SPAN = 0, (None, None)


class WettedAreas(sequencetools.FactorSequence):
    """Wetted area of each trapeze range [m²]."""

    NDIM, SPAN = 1, (0.0, None)


class WettedArea(sequencetools.FactorSequence):
    """Total wetted area [m²]."""

    NDIM, SPAN = 0, (0.0, None)


class WettedPerimeters(sequencetools.FactorSequence):
    """Wetted perimeter of each trapeze range [m]."""

    NDIM, SPAN = 1, (0.0, None)


class WettedPerimeterDerivatives(sequencetools.FactorSequence):
    """Change in the wetted perimeter of each trapeze range with respect to a water
    level increase [-]."""

    NDIM, SPAN = 1, (0.0, None)


class SurfaceWidths(sequencetools.FactorSequence):
    """Surface width of each trapeze range [m]."""

    NDIM, SPAN = 1, (0.0, None)


class SurfaceWidth(sequencetools.FactorSequence):
    """Total surface width [m]."""

    NDIM, SPAN = 0, (0.0, None)


class DischargeDerivatives(sequencetools.FactorSequence):
    """Discharge change of each trapeze range with respect to a water level increase
    [m²/s]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)


class DischargeDerivative(sequencetools.FactorSequence):
    """Total discharge change with respect to a water level increase [m²/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class Celerity(sequencetools.FactorSequence):
    """Kinematic celerity (wave speed) [m/s]."""

    NDIM, SPAN = 0, (None, None)
