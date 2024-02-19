# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

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
        r"""Trim values in accordance with :math:`SInz / PWMax \leq STInz \leq SInz`, or
        at least in accordance with if :math:`STInz \geq 0`.

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(7)
        >>> pwmax(2.0)
        >>> states.stinz(-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0)
        >>> states.stinz
        stinz(0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0)

        >>> states.sinz = -1.0, 0.0, 1.0, 5.0, 10.0, 20.0, 3.0
        >>> states.stinz(-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0)
        >>> states.stinz
        stinz(0.0, 0.0, 0.5, 5.0, 5.0, 10.0, 3.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        sinz = numpy.clip(self.subseqs.sinz.values, 0.0, numpy.inf)
        if lower is None:
            lower = sinz / pwmax
            lower[numpy.isnan(lower)] = 0.0
        if upper is None:
            upper = sinz
        super().trim(lower, upper)


class SInz(lland_sequences.State1DSequence):
    """Wasseräquivalent Gesamtschnee im Interzeptionsspeicher (frozen water equivalent
    of the intercepted snow) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Forest()

    def trim(self, lower=None, upper=None):
        r"""Trim values in accordance with :math:`SInz / PWMax \leq STInz \leq SInz`, or
        at least in accordance with if :math:`SInz \geq 0`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> pwmax(2.0)
        >>> states.sinz(-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0)
        >>> states.sinz
        sinz(0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0)

        >>> states.stinz = -1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0
        >>> states.sinz(-1.0, 0.0, 1.0, 5.0, 10.0, 20.0, 3.0)
        >>> states.sinz
        sinz(0.0, 0.0, 0.0, 5.0, 10.0, 10.0, 5.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        stinz = numpy.clip(self.subseqs.stinz, 0.0, numpy.inf)
        if upper is None:
            upper = pwmax * stinz
        if lower is None:
            lower = stinz
            lower[numpy.isnan(lower)] = 0.0
        super().trim(lower, upper)


class ESnowInz(lland_sequences.State1DSequence):
    """Kälteinhalt der Schneedecke des Interzeptionsspeichers [WT/m²]."""

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
        r"""Trim values in accordance with :math:`WAeS / PWMax \leq WATS \leq WAeS`, or
        at least in accordance with if :math:`WATS \geq 0`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> pwmax(2.0)
        >>> states.wats(-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0)
        >>> states.wats
        wats(0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0)

        >>> states.waes = -1.0, 0.0, 1.0, 5.0, 10.0, 20.0, 3.0
        >>> states.wats(-1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0)
        >>> states.wats
        wats(0.0, 0.0, 0.5, 5.0, 5.0, 10.0, 3.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        waes = numpy.clip(self.subseqs.waes.values, 0.0, numpy.inf)
        if lower is None:
            lower = waes / pwmax
            lower[numpy.isnan(lower)] = 0.0
        if upper is None:
            upper = waes
        super().trim(lower, upper)


class WAeS(lland_sequences.State1DSequence):
    """Wasseräquivalent Gesamtschnee auf der Bodenoberfläche (total water equivalent
    of the snow cover) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()

    def trim(self, lower=None, upper=None):
        r"""Trim values in accordance with :math:`WAeS / PWMax \leq WATS \leq WAeS`, or
        at least in accordance with if :math:`WAeS \geq 0`


        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(7)
        >>> pwmax(2.0)
        >>> states.waes(-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0)
        >>> states.waes
        waes(0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0)

        >>> states.wats = -1.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0
        >>> states.waes(-1.0, 0.0, 1.0, 5.0, 10.0, 20.0, 3.0)
        >>> states.waes
        waes(0.0, 0.0, 0.0, 5.0, 10.0, 10.0, 5.0)
        """
        pwmax = self.subseqs.seqs.model.parameters.control.pwmax
        wats = numpy.clip(self.subseqs.wats, 0.0, numpy.inf)
        if upper is None:
            upper = pwmax * wats
        if lower is None:
            lower = wats
            lower[numpy.isnan(lower)] = 0.0
        super().trim(lower, upper)


class ESnow(lland_sequences.State1DSequence):
    """Thermischer Energieinhalt der Schneedecke bezogen auf 0°C (thermal
    energy content of the snow layer with respect to 0°C) [WT/m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)
    mask = lland_masks.Land()


class TauS(lland_sequences.State1DSequence):
    """Dimensionsloses Alter der Schneedecke (dimensionless age of the snow layer) [-].

    If there is no snow-layer, the value of |TauS| is |numpy.nan|.
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()


class EBdn(lland_sequences.State1DSequence):
    """Energiegehalt des Bodenwassers (energy content of the soil water)
    [WT/m²]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)
    mask = lland_masks.Land()


class BoWa(lland_sequences.State1DSequence):
    """Bodenwasserspeicherung (soil water storage) [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Soil()

    def trim(self, lower=None, upper=None):
        r"""Trim in accordance with :math:`0 \leq BoWa \leq WMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> wmax(200.0)
        >>> states.bowa(-100.0, 0.0, 100.0, 200.0, 300.0)
        >>> states.bowa
        bowa(0.0, 0.0, 100.0, 200.0, 200.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.wmax
        super().trim(lower, upper)


class SDG1(sequencetools.StateSequence):
    """Träger Direktabfluss-Gebietsspeicher (slow direct runoff storage) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class SDG2(sequencetools.StateSequence):
    """Dynamischer Direktabfluss-Gebietsspeicher (fast direct runoff storage) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class SIG1(sequencetools.StateSequence):
    """Erster Zwischenabfluss-Gebietsspeicher (first interflow storage) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class SIG2(sequencetools.StateSequence):
    """Zweiter Zwischenabfluss-Gebietsspeicher (second interflow storage) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class SBG(sequencetools.StateSequence):
    """Basisabfluss-Gebietsspeicher (base flow storage) [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)

    def trim(self, lower=None, upper=None):
        r"""Trim in accordance with :math:`SBG \leq GSBMax \cdot VolBMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> volbmax(10.0)
        >>> gsbmax(2.0)
        >>> states.sbg(10.0)
        >>> states.sbg
        sbg(10.0)
        >>> states.sbg(21.0)
        >>> states.sbg
        sbg(20.0)
        """
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            upper = control.gsbmax.value * control.volbmax.value
        super().trim(lower, upper)
