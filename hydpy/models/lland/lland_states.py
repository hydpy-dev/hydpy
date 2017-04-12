# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools

class Inzp(sequencetools.StateSequence):
    """Interzeptionsspeicherung (interception storage) [mm].

    Note that :class:`Inzp` of HydPy-L implements no specialized trim method
    (as opposed to :class:`~hydpy.models.hland.hland_states.Ic` of HydPy-H).
    This is due the discontinuous evolution of
    :class:`~hydpy.models.lland.lland_control.IcC` in time.  In accordance
    with the orginal LARSIM implementation, :class:`Inzp` can be temporarily
    overfilled during rain periods whenever
    :class:`~hydpy.models.lland.lland_control.IcC` drops rapidly between two
    months.  A specialized trim method would just make the excess water
    vanish.  But in HydPy-L, the excess water becomes
    :class:`~hydpy.models.lland.lland_fluxes.ThruFall` in the first simulation
    step of the new month.
    """
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class WATS(sequencetools.StateSequence):
    """Wasseräquivalent Trockenschnee (frozen water equivalent of the snow
    cover) [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class WAeS(sequencetools.StateSequence):
    """Wasseräquivalent Gesamtschnee (total water equivalent of the snow
    cover) [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class BoWa(sequencetools.StateSequence):
    """Bodenwasserspeicherung (soil water storage) [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class WRel(sequencetools.StateSequence):
    """Relative Bodenfeuchte (relative soil moisture) [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., 1.)

class QDGZ(sequencetools.StateSequence):
    """Zufluss in den Direktabfluss-Gebietsspeicher (inflow into the
    storage compartment for direct runoff) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QIGZ1(sequencetools.StateSequence):
    """"Zufluss in den ersten Zwischenabfluss-Gebietsspeicher (inflow into the
    first storage compartment for interflow) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QIGZ2(sequencetools.StateSequence):
    """Zufluss in den zweiten Zwischenabfluss-Gebietsspeicher (inflow into the
    second storage compartment for interflow) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QBGZ(sequencetools.StateSequence):
    """Zufluss in den Basisabfluss-Gebietsspeicher (inflow into the
    storage compartment for base flow) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QDGA(sequencetools.StateSequence):
    """Abfluss aus dem Direktabfluss-Gebietsspeicher (outflow from the
    storage compartment for direct runoff) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QIGA1(sequencetools.StateSequence):
    """Abfluss aus dem "unteren" Zwischenabfluss-Gebietsspeicher (outflow from 
    the storage compartment for the first interflow component) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QIGA2(sequencetools.StateSequence):
    """Abfluss aus dem "oberen" Zwischenabfluss-Gebietsspeicher (outflow from 
    the storage compartment for the second interflow component) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)
    
class QBGA(sequencetools.StateSequence):
    """Abfluss aus dem Basisabfluss-Gebietsspeicher (outflow from the
    storage compartment for base flow) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class StateSequences(sequencetools.StateSequences):
    """State sequences of the HydPy-L-Land model."""
    _SEQCLASSES = (Inzp, WATS, WAeS, BoWa, WRel,
                   QDGZ, QIGZ1, QIGZ2, QBGZ, QDGA, QIGA1, QIGA2, QBGA)