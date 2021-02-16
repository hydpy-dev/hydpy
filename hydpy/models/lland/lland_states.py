# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import sequencetools

# ...from lland
from hydpy.models.lland import lland_masks
from hydpy.models.lland import lland_sequences


class Inzp(lland_sequences.State1DSequence):
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

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()


class STInz(lland_sequences.State1DSequence):
    """Wasseräquivalent Trockenschnee im Interzeptionsspeicher (total water equivalent
    of the intercepted snow) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Forest()

    def trim(self, lower=None, upper=None):
        r"""Trim values in accordance with :math:`SInz \leq PWMax \cdot STInz`,
        or at least in accordance with if :math:`STInz \geq 0`.

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(7)
        >>> pwmax(2.0)
        >>> states.sinz = -1.0, 0.0, 1.0, -1.0, 5.0, 10.0, 20.0
        >>> states.stinz(-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0)
        >>> states.stinz
        stinz(0.0, 0.0, 0.5, 5.0, 5.0, 5.0, 10.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        sinz = self.subseqs.sinz
        if lower is None:
            lower = numpy.clip(sinz / pwmax, 0.0, numpy.inf)
            lower[numpy.isnan(lower)] = 0.0
        super().trim(lower, upper)


class SInz(lland_sequences.State1DSequence):
    """Wasseräquivalent Gesamtschnee im Interzeptionsspeicher (frozen water equivalent
    of the intercepted snow) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Forest()

    def trim(self, lower=None, upper=None):
        r"""Trim values in accordance with :math:`0 \leq SInz \leq PWMax \cdot STInz`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> pwmax(2.0)
        >>> states.stinz = 0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0
        >>> states.sinz(-1.0, 0.0, 1.0, -1.0, 5.0, 10.0, 20.0)
        >>> states.sinz
        sinz(0.0, 0.0, 0.0, 0.0, 5.0, 10.0, 10.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        stinz = self.subseqs.stinz
        if upper is None:
            upper = pwmax * stinz
        super().trim(lower, upper)


class ESnowInz(lland_sequences.State1DSequence):
    """Kälteinhalt der Schneedecke des Interzeptionsspeichers [MJ/m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)
    mask = lland_masks.Forest()


class ASInz(lland_sequences.State1DSequence):
    """Dimensionsloses Alter des interzipierten Schnees (dimensionless age of the
    intercepted snow layer) [-].

    If there is no intercepted snow, the value of |ASInz| is |numpy.nan|.
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Forest()


class WATS(lland_sequences.State1DSequence):
    """Wasseräquivalent Trockenschnee auf der Bodenoberfläche (frozen water equivalent
    of the snow cover) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`WAeS \\leq PWMax \\cdot WATS`,
        or at least in accordance with if :math:`WATS \\geq 0`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
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
            lower = numpy.clip(waes / pwmax, 0.0, numpy.inf)
            lower[numpy.isnan(lower)] = 0.0
        super().trim(lower, upper)


class WAeS(lland_sequences.State1DSequence):
    """Wasseräquivalent Gesamtschnee auf der Bodenoberfläche (total water equivalent
    of the snow cover) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`WAeS \\leq PWMax \\cdot WATS`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
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
            upper = pwmax * wats
        super().trim(lower, upper)


class ESnow(lland_sequences.State1DSequence):
    """Thermischer Energieinhalt der Schneedecke bezogen auf 0°C (thermal
    energy content of the snow layer with respect to 0°C) [MJ/m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)
    mask = lland_masks.Land()


class TauS(lland_sequences.State1DSequence):
    """Dimensionsloses Alter der Schneedecke (dimensionless age of the snow
    layer) [-].

    If there is no snow-layer, the value of |TauS| is |numpy.nan|.
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()


class EBdn(lland_sequences.State1DSequence):
    """Energiegehalt des Bodenwassers (energy content of the soil water)
    [MJ/m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)
    mask = lland_masks.Land()


class BoWa(lland_sequences.State1DSequence):
    """Bodenwasserspeicherung (soil water storage) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Soil()

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`BoWa \\leq WMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> wmax(200.)
        >>> states.bowa(-100.,0., 100., 200., 300.)
        >>> states.bowa
        bowa(0.0, 0.0, 100.0, 200.0, 200.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.wmax
        super().trim(lower, upper)


class QDGZ1(sequencetools.StateSequence):
    """Zufluss in den trägeren Direktabfluss-Gebietsspeicher (inflow into
    the less responsive storage compartment for direct runoff) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class QDGZ2(sequencetools.StateSequence):
    """Zufluss in den dynamischeren Direktabfluss-Gebietsspeicher (inflow into
    the more responsive storage compartment for direct runoff) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class QIGZ1(sequencetools.StateSequence):
    """ "Zufluss in den ersten Zwischenabfluss-Gebietsspeicher (inflow into the
    first storage compartment for interflow) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class QIGZ2(sequencetools.StateSequence):
    """Zufluss in den zweiten Zwischenabfluss-Gebietsspeicher (inflow into the
    second storage compartment for interflow) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class QBGZ(sequencetools.StateSequence):
    """Zufluss in den Basisabfluss-Gebietsspeicher (inflow into the
    storage compartment for base flow) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class QDGA1(sequencetools.StateSequence):
    """Abfluss aus dem trägeren Direktabfluss-Gebietsspeicher (outflow from
    the less responsive storage compartment for direct runoff) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class QDGA2(sequencetools.StateSequence):
    """Abfluss aus dem dynamischeren Direktabfluss-Gebietsspeicher (outflow
    from the more responsive storage compartment for direct runoff) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class QIGA1(sequencetools.StateSequence):
    """Abfluss aus dem "unteren" Zwischenabfluss-Gebietsspeicher (outflow from
    the storage compartment for the first interflow component) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class QIGA2(sequencetools.StateSequence):
    """Abfluss aus dem "oberen" Zwischenabfluss-Gebietsspeicher (outflow from
    the storage compartment for the second interflow component) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class QBGA(sequencetools.StateSequence):
    """Abfluss aus dem Basisabfluss-Gebietsspeicher (outflow from the
    storage compartment for base flow) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
