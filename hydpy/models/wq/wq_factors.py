# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from wq
from hydpy.models.wq import wq_variables


class WaterDepth(sequencetools.FactorSequence):
    """Water depth [m]."""

    NDIM, SPAN = 0, (0.0, None)


class WaterLevel(sequencetools.FactorSequence):
    """Water level [m]."""

    NDIM, SPAN = 0, (None, None)


class WettedAreas(wq_variables.MixinTrapezes, sequencetools.FactorSequence):
    """Wetted area of each trapeze range [m²]."""

    SPAN = (0.0, None)


class WettedArea(sequencetools.FactorSequence):
    """Total wetted area [m²]."""

    NDIM, SPAN = 0, (0.0, None)


class FlowAreas(wq_variables.MixinTrapezesSectors, sequencetools.FactorSequence):
    """The flow area of each cross section sector [m²]."""

    SPAN = (0.0, None)


class FlowArea(sequencetools.FactorSequence):
    """The flow area of the complete cross section [m²]."""

    NDIM, SPAN = 0, (0.0, None)


class TotalAreas(wq_variables.MixinTrapezesSectors, sequencetools.FactorSequence):
    """The total wetted area of the complete cross section [m²]."""

    SPAN = (0.0, None)


class TotalArea(sequencetools.FactorSequence):
    """Total wetted area [m²]."""

    NDIM, SPAN = 0, (0.0, None)


class WettedPerimeters(wq_variables.MixinTrapezes, sequencetools.FactorSequence):
    """Wetted perimeter of each trapeze range [m]."""

    SPAN = (0.0, None)


class FlowPerimeters(wq_variables.MixinTrapezesSectors, sequencetools.FactorSequence):
    """Flow perimeter of each cross section sector [m]."""

    SPAN = (0.0, None)


class WettedPerimeter(sequencetools.FactorSequence):
    """Total wetted perimeter [m]."""

    NDIM, SPAN = 0, (0.0, None)


class WettedPerimeterDerivatives(
    wq_variables.MixinTrapezes, sequencetools.FactorSequence
):
    """Change in the wetted perimeter of each trapeze range with respect to a water
    level increase [-]."""

    SPAN = (0.0, None)


class SurfaceWidths(wq_variables.MixinTrapezes, sequencetools.FactorSequence):
    """Surface width of each trapeze range [m]."""

    SPAN = (0.0, None)


class SurfaceWidth(sequencetools.FactorSequence):
    """Total surface width [m]."""

    NDIM, SPAN = 0, (0.0, None)


class FlowWidths(wq_variables.MixinTrapezesSectors, sequencetools.FactorSequence):
    """Flow surface width of each cross section sector [m]."""

    SPAN = (0.0, None)


class TotalWidths(wq_variables.MixinTrapezesSectors, sequencetools.FactorSequence):
    """Total surface width of each cross section sector [m]."""

    SPAN = (0.0, None)


class DischargeDerivatives(wq_variables.MixinTrapezes, sequencetools.FactorSequence):
    """Discharge change of each trapeze range with respect to a water level increase
    [m²/s]."""

    NUMERIC, SPAN = False, (None, None)


class DischargeDerivative(sequencetools.FactorSequence):
    """Total discharge change with respect to a water level increase [m²/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class Celerity(sequencetools.FactorSequence):
    """Kinematic celerity (wave speed) [m/s]."""

    NDIM, SPAN = 0, (None, None)
