# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Inflow(sequencetools.FluxSequence):
    """Total inflow [m³/s]."""
    NDIM, NUMERIC = 0, True


class FloodDischarge(sequencetools.FluxSequence):
    """Water release associated with flood events [m³/s]."""
    NDIM, NUMERIC = 0, True


class TotalRemoteDischarge(sequencetools.FluxSequence):
    """Total discharge at a cross section far downstream [m³/s]."""
    NDIM, NUMERIC = 0, False


class NaturalRemoteDischarge(sequencetools.FluxSequence):
    """Natural discharge at a cross section far downstream [m³/s].

    `Natural` means: without the water released by the dam.
    """
    NDIM, NUMERIC = 0, False


class RemoteDemand(sequencetools.FluxSequence):
    """Discharge demand at a cross section far downstream [m³/s]."""
    NDIM, NUMERIC = 0, False


class RemoteFailure(sequencetools.FluxSequence):
    """Difference between the the actual and the required discharge at
    a cross section far downstream [m³/s]."""
    NDIM, NUMERIC = 0, False


class RequiredRemoteRelease(sequencetools.FluxSequence):
    """Water release considered appropriate to reduce drought events
    at cross sections far downstream to the desired degree [m³/s]."""
    NDIM, NUMERIC = 0, False


class AllowedRemoteRelieve(sequencetools.FluxSequence):
    """Water release to a remote location to relieve the dam during high
    flow conditions, allowed by the remote location [m³/s]."""
    NDIM, NUMERIC = 0, False


class PossibleRemoteRelieve(sequencetools.FluxSequence):
    """Maximum possible water release to a remote location to relieve the
    dam during high flow conditions [m³/s]."""
    NDIM, NUMERIC = 0, True


class ActualRemoteRelieve(sequencetools.FluxSequence):
    """Actual water release to a remote location to relieve the
    dam during high flow conditions [m³/s]."""
    NDIM, NUMERIC = 0, True


class RequiredRelease(sequencetools.FluxSequence):
    """Required water release for reducing drought events downstream [m³/s]."""
    NDIM, NUMERIC = 0, False


class TargetedRelease(sequencetools.FluxSequence):
    """The targeted water release for reducing drought events downstream
    after taking both the required release and additional low flow
    regulations into account [m³/s]."""
    NDIM, NUMERIC = 0, False


class ActualRelease(sequencetools.FluxSequence):
    """Actual water release thought for reducing drought events
    downstream [m³/s]."""
    NDIM, NUMERIC = 0, True


class ActualRemoteRelease(sequencetools.FluxSequence):
    """Actual water release thought for arbitrary "remote" purposes [m³/s]."""
    NDIM, NUMERIC = 0, True


class Outflow(sequencetools.FluxSequence):
    """Total outflow [m³/s]."""
    NDIM, NUMERIC = 0, True


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the dam model."""
    _SEQCLASSES = (Inflow,
                   TotalRemoteDischarge,
                   NaturalRemoteDischarge,
                   RemoteDemand,
                   RemoteFailure,
                   RequiredRemoteRelease,
                   AllowedRemoteRelieve,
                   PossibleRemoteRelieve,
                   ActualRemoteRelieve,
                   RequiredRelease,
                   TargetedRelease,
                   ActualRelease,
                   ActualRemoteRelease,
                   FloodDischarge,
                   Outflow)
