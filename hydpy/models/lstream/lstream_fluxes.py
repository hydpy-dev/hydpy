# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class QRef(sequencetools.FluxSequence):
    """Referenzabfluss (reference flow) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class H(sequencetools.FluxSequence):
    """Wasserstand (water stage) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AM(sequencetools.FluxSequence):
    """Durchflossene Fläche Hauptgerinne (flown through area of the
    main channel) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AV(sequencetools.LeftRightSequence):
    """Durchflossene Fläche Vorländer (flown through area of both forelands)
    [m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class AVR(sequencetools.LeftRightSequence):
    """Durchflossene Fläche Vorlandränder (flown through area of both outer
    embankments) [m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class AG(sequencetools.FluxSequence):
    """Durchflossene Fläche gesamt  (total flown through area) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UM(sequencetools.FluxSequence):
    """Benetzter Umfang Hauptgerinne (wetted perimeter of the
    main channel) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UV(sequencetools.LeftRightSequence):
    """Benetzter Umfang Vorländer (wetted perimeter of both forelands) [m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class UVR(sequencetools.LeftRightSequence):
    """Benetzter Umfang Vorlandränder (wetted perimeter of both outer
    embankments) [m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class UG(sequencetools.FluxSequence):
    """Durchflossene Fläche gesamt  (total wetted perimeter) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAM(sequencetools.FluxSequence):
    """Ableitung von :class:`AM` (derivative of :class:`AM`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAV(sequencetools.LeftRightSequence):
    """Ableitung von :class:`AV` (derivative of :class:`AV`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DAVR(sequencetools.LeftRightSequence):
    """Ableitung von :class:`AVR` (derivative of :class:`AVR`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DAG(sequencetools.FluxSequence):
    """Ableitung von :class:`AG` (derivative of :class:`AG`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUM(sequencetools.FluxSequence):
    """Ableitung von :class:`UM` (derivative of :class:`UM`) [m/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUV(sequencetools.LeftRightSequence):
    """Ableitung von :class:`UV` (derivative of :class:`UV`) [m/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DUVR(sequencetools.LeftRightSequence):
    """Ableitung von :class:`UVR` (derivative of :class:`UVR`) [m/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DUG(sequencetools.FluxSequence):
    """Ableitung von :class:`UG` (derivative of :class:`UG`) [m/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QM(sequencetools.FluxSequence):
    """Durchfluss Hauptgerinne (discharge of the main channel) [m³]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QV(sequencetools.LeftRightSequence):
    """Durchfluss Voränder (discharge of both forelands) [m³]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class QVR(sequencetools.LeftRightSequence):
    """Durchfluss Vorlandränder (discharge of both outer embankment) [m³]."""
    NDIM, NUMERIC, SPAN = 1, False, (1., None)

class QG(sequencetools.FluxSequence):
    """Durchfluss gesamt  (total discharge) [m³]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQM(sequencetools.FluxSequence):
    """Ableitung von :class:`QM` (derivative of :class:`QM`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQV(sequencetools.LeftRightSequence):
    """Ableitung von :class:`QV` (derivative of :class:`QV`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DQVR(sequencetools.LeftRightSequence):
    """Ableitung von :class:`QVR` (derivative of :class:`QVR`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DQG(sequencetools.FluxSequence):
    """Ableitung von :class:`QG` (derivative of :class:`QG`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class RK(sequencetools.FluxSequence):
    """Schwerpunktlaufzeit (traveling time) [s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-L-Stream."""
    _SEQCLASSES = (QRef, H,
                   AM, AV, AVR, AG, UM, UV, UVR, UG,
                   DAM, DAV, DAVR, DAG, DUM, DUV, DUVR, DUG,
                   QM, QV, QVR, QG, DQM, DQV, DQVR, DQG,
                   RK)
