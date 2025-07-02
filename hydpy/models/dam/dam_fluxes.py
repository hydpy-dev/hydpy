# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Precipitation(sequencetools.FluxSequence):
    """Precipitation [mm]."""

    NDIM, NUMERIC = 0, False


class AdjustedPrecipitation(sequencetools.FluxSequence):
    """Adjusted precipitation [m³/s]."""

    NDIM, NUMERIC = 0, True


class PotentialEvaporation(sequencetools.FluxSequence):
    """Potential evaporation [mm/T]."""

    NDIM, NUMERIC = 0, False


class AdjustedEvaporation(sequencetools.FluxSequence):
    """Adjusted evaporation [m³/s]."""

    NDIM, NUMERIC = 0, False


class ActualEvaporation(sequencetools.FluxSequence):
    """Actual evaporation [m³/s]."""

    NDIM, NUMERIC = 0, True


class Inflow(sequencetools.FluxSequence):
    """Total inflow [m³/s]."""

    NDIM, NUMERIC = 0, True


class Exchange(sequencetools.FluxSequence):
    """Water exchange with another location [m³/s]."""

    NDIM, NUMERIC = 0, True


class TotalRemoteDischarge(sequencetools.FluxSequence):
    """Total discharge at a cross-section far downstream [m³/s]."""

    NDIM, NUMERIC = 0, False


class NaturalRemoteDischarge(sequencetools.FluxSequence):
    """Natural discharge at a cross-section far downstream [m³/s].

    `Natural` means: without the water released by the dam.
    """

    NDIM, NUMERIC = 0, False


class RemoteDemand(sequencetools.FluxSequence):
    """Discharge demand at a cross-section far downstream [m³/s]."""

    NDIM, NUMERIC = 0, False


class RemoteFailure(sequencetools.FluxSequence):
    """Difference between the actual and the required discharge at a cross-section far
    downstream [m³/s]."""

    NDIM, NUMERIC = 0, False


class RequiredRemoteRelease(sequencetools.FluxSequence):
    """Water release considered appropriate to reduce drought events at cross-sections
    far downstream [m³/s]."""

    NDIM, NUMERIC = 0, False


class AllowedRemoteRelief(sequencetools.FluxSequence):
    """Allowed discharge to relieve a dam during high flow conditions [m³/s]."""

    NDIM, NUMERIC = 0, False


class RequiredRemoteSupply(sequencetools.FluxSequence):
    """Required water supply, for example, to fill a dam during low water conditions
    [m³/s]."""

    NDIM, NUMERIC = 0, False


class PossibleRemoteRelief(sequencetools.FluxSequence):
    """Maximum possible water release to a remote location to relieve the dam during
    high flow conditions [m³/s]."""

    NDIM, NUMERIC = 0, True


class ActualRemoteRelief(sequencetools.FluxSequence):
    """Actual water release to a remote location to relieve the dam during high flow
    conditions [m³/s]."""

    NDIM, NUMERIC = 0, True


class RequiredRelease(sequencetools.FluxSequence):
    """Required water release for reducing drought events downstream [m³/s]."""

    NDIM, NUMERIC = 0, False


class TargetedRelease(sequencetools.FluxSequence):
    """The targeted water release for reducing drought events downstream after taking
    both the required release and additional low flow regulations into account
    [m³/s]."""

    NDIM, NUMERIC = 0, False


class ActualRelease(sequencetools.FluxSequence):
    """Actual water release thought for reducing drought events downstream [m³/s]."""

    NDIM, NUMERIC = 0, True


class MissingRemoteRelease(sequencetools.FluxSequence):
    """Amount of the required remote demand not met by the actual release [m³/s]."""

    NDIM, NUMERIC = 0, False


class ActualRemoteRelease(sequencetools.FluxSequence):
    """Actual water release thought for arbitrary "remote" purposes [m³/s]."""

    NDIM, NUMERIC = 0, True


class SafeRelease(sequencetools.FluxSequence):
    """Water release that is considered safe in terms of flood protection [m³/s]."""

    NDIM, NUMERIC = 0, False


class AimedRelease(sequencetools.FluxSequence):
    """Ideal controlled water release [m³/s]."""

    NDIM, NUMERIC = 0, False


class UnavoidableRelease(sequencetools.FluxSequence):
    """Water release that cannot be avoided due to limited storage capacity [m³/s]."""

    NDIM, NUMERIC = 0, True


class FloodDischarge(sequencetools.FluxSequence):
    """Water release associated with flood events [m³/s]."""

    NDIM, NUMERIC = 0, True


class FreeDischarge(sequencetools.FluxSequence):
    """Free water release through structures as flap sluice gates [m³/s]."""

    NDIM, NUMERIC = 0, True


class MaxForcedDischarge(sequencetools.FluxSequence):
    """The currently highest possible forced water release through structures as pumps
    [m³/s]."""

    NDIM, NUMERIC = 0, True


class MaxFreeDischarge(sequencetools.FluxSequence):
    """The currently highest possible free water release through structures as pumps
    [m³/s]."""

    NDIM, NUMERIC = 0, True


class ForcedDischarge(sequencetools.FluxSequence):
    """Forced water release through structures as pumps [m³/s]."""

    NDIM, NUMERIC = 0, True


class Outflow(sequencetools.FluxSequence):
    """Total outflow [m³/s]."""

    NDIM, NUMERIC = 0, True
