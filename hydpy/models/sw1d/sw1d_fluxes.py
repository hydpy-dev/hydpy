# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Inflow(sequencetools.FluxSequence):
    """Longitudinal flow into the first channel segment [m³/s]."""

    NDIM = 0
    NUMERIC = False


class Outflow(sequencetools.FluxSequence):
    """Longitudinal flow out of the last channel segment [m³/s]."""

    NDIM = 0
    NUMERIC = False


class LateralFlow(sequencetools.FluxSequence):
    """Lateral flow into the first channel segment [m³/s]."""

    NDIM = 0
    NUMERIC = False


class NetInflow(sequencetools.FluxSequence):
    """The net inflow into a channel segment [m³/T]."""

    NDIM = 0
    NUMERIC = False


class DischargeUpstream(sequencetools.FluxSequence):
    """The summed (partial) of all upstream routing models [m³/s]."""

    NDIM = 0
    NUMERIC = False


class DischargeDownstream(sequencetools.FluxSequence):
    """The summed (partial) of all downstream routing models [m³/s]."""

    NDIM = 0
    NUMERIC = False


class DischargeVolume(sequencetools.FluxSequence):
    """The total amount of discharge of a simulation step [m³/T]."""

    NDIM = 0
    NUMERIC = False


class Discharges(sequencetools.FluxSequence):
    """The discharges between all channel segments, including the flow into the first
    and out of the last one [m³/s]."""

    NDIM = 1
    NUMERIC = False
    PLUS = 1
