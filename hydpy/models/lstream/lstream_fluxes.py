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
    """Durchfluss gesamt (total discharge) [m³]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class RK(sequencetools.FluxSequence):
    """Schwerpunktlaufzeit (traveling time) [s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-L-Stream."""
    _SEQCLASSES = (QRef, H, AM, AV, AVR, AG, UM, UV, UVR, UG,
                   QM, QV, QVR, QG, RK)
