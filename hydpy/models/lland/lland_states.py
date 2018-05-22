# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...HydPy specific
from hydpy.core import sequencetools


class Inzp(sequencetools.StateSequence):
    """Interzeptionsspeicherung (interception storage) [mm].

    Note that |Inzp| of HydPy-L implements no specialized trim method
    (as opposed to |hland_states.Ic| of |hland|).  This is due the
    discontinuous evolution of |KInz| in time.  In accordance with the
    original LARSIM implementation, |Inzp| can be temporarily overfilled
    during rain periods whenever |KInz| drops rapidly between two months.
    A specialized trim method would just make the excess water vanish.
    But in HydPy-L, the excess water becomes |NBes| in the first
    simulation step of the new month.
    """
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class WATS(sequencetools.StateSequence):
    """Wasseräquivalent Trockenschnee (frozen water equivalent of the snow
    cover) [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`WAeS \\leq PWMax \\cdot WATS`,
        or at least in accordance with if :math:`WATS \\geq 0`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> pwmax(2.0)
        >>> states.waes = -1., 0., 1., -1., 5., 10., 20.
        >>> states.wats(-1., 0., 0., 5., 5., 5., 5.)
        >>> states.wats
        wats(0.0, 0.0, 0.5, 5.0, 5.0, 5.0, 10.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        waes = self.subseqs.waes
        if lower is None:
            lower = numpy.clip(waes/pwmax, 0., numpy.inf)
            lower[numpy.isnan(lower)] = 0.0
        sequencetools.StateSequence.trim(self, lower, upper)


class WAeS(sequencetools.StateSequence):
    """Wasseräquivalent Gesamtschnee (total water equivalent of the snow
    cover) [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`WAeS \\leq PWMax \\cdot WATS`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(7)
        >>> pwmax(2.)
        >>> states.wats = 0., 0., 0., 5., 5., 5., 5.
        >>> states.waes(-1., 0., 1., -1., 5., 10., 20.)
        >>> states.waes
        waes(0.0, 0.0, 0.0, 0.0, 5.0, 10.0, 10.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        wats = self.subseqs.wats
        if upper is None:
            upper = pwmax*wats
        sequencetools.StateSequence.trim(self, lower, upper)


class BoWa(sequencetools.StateSequence):
    """Bodenwasserspeicherung (soil water storage) [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`BoWa \\leq NFk`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> nfk(200.)
        >>> states.bowa(-100.,0., 100., 200., 300.)
        >>> states.bowa
        bowa(0.0, 0.0, 100.0, 200.0, 200.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.nfk
        sequencetools.StateSequence.trim(self, lower, upper)


class QDGZ1(sequencetools.StateSequence):
    """Zufluss in den trägeren Direktabfluss-Gebietsspeicher (inflow into
    the less responsive storage compartment for direct runoff) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class QDGZ2(sequencetools.StateSequence):
    """Zufluss in den dynamischeren Direktabfluss-Gebietsspeicher (inflow into
    the more responsive storage compartment for direct runoff) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (None, None)


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
    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class QDGA1(sequencetools.StateSequence):
    """Abfluss aus dem trägeren Direktabfluss-Gebietsspeicher (outflow from
    the less responsive storage compartment for direct runoff) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)


class QDGA2(sequencetools.StateSequence):
    """Abfluss aus dem dynamischeren Direktabfluss-Gebietsspeicher (outflow
    from the more responsive storage compartment for direct runoff) [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (None, None)


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
    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class StateSequences(sequencetools.StateSequences):
    """State sequences of the HydPy-L-Land model."""
    _SEQCLASSES = (Inzp,
                   WATS,
                   WAeS,
                   BoWa,
                   QDGZ1,
                   QDGZ2,
                   QIGZ1,
                   QIGZ2,
                   QBGZ,
                   QDGA1,
                   QDGA2,
                   QIGA1,
                   QIGA2,
                   QBGA)
