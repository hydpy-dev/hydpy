# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.hland import hland_control
from hydpy.models.hland import hland_masks
from hydpy.models.hland import hland_sequences
from hydpy.models.hland.hland_constants import ILAKE


class Ic(hland_sequences.State1DSequence):
    """Interception storage [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = hland_masks.Interception()

    CONTROLPARAMETERS = (hland_control.IcMax,)

    def trim(self, lower=None, upper=None):
        r"""Trim |Ic| following :math:`0 \leq IC \leq ICMAX`.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> icmax(2.0)
        >>> states.ic(-1.0, 0.0, 1.0, 2.0, 3.0)
        >>> states.ic
        ic(0.0, 0.0, 1.0, 2.0, 2.0)
        """
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            upper = control.icmax
        super().trim(lower, upper)


class SP(hland_sequences.State1DSequence):
    """Frozen water stored in the snow layer [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (None, None)
    mask = hland_masks.Snow()

    CONTROLPARAMETERS = (hland_control.WHC,)

    def trim(self, lower=None, upper=None):
        r"""Trim |SP| following :math:`WC \leq WHC \cdot SP`.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> whc(0.1)
        >>> states.sp(-1., 0., 0., 5., 5., 5., 5.)
        >>> states.sp
        sp(0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0)
        >>> states.wc.values = -1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0
        >>> states.sp(-1., 0., 0., 5., 5., 5., 5.)
        >>> states.sp
        sp(0.0, 0.0, 10.0, 5.0, 5.0, 5.0, 10.0)
        """
        whc = self.subseqs.seqs.model.parameters.control.whc
        wc = self.subseqs.wc
        if lower is None:
            wc_values = wc.values.copy()
            wc_values[numpy.isnan(wc_values)] = 0.0
            with numpy.errstate(divide="ignore", invalid="ignore"):
                lower = numpy.clip(wc_values / whc.values, 0.0, numpy.inf)
        super().trim(lower, upper)


class WC(hland_sequences.State1DSequence):
    """Liquid water content of the snow layer [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = hland_masks.Snow()

    CONTROLPARAMETERS = (hland_control.WHC,)

    def trim(self, lower=None, upper=None):
        """Trim |WC| following :math:`WC \\leq WHC \\cdot SP`.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> whc(0.1)
        >>> states.sp = 0.0, 0.0, 0.0, 5.0, 5.0, 5.0, 5.0
        >>> states.wc(-1.0, 0.0, 1.0, -1.0, 0.0, 0.5, 1.0)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5)
        """
        whc = self.subseqs.seqs.model.parameters.control.whc
        sp = self.subseqs.sp
        if upper is None:
            upper = whc * sp
        super().trim(lower, upper)


class SM(hland_sequences.State1DSequence):
    """Soil moisture [mm].

    Note that PREVAH uses the abbreviation `SSM`, and COSERO uses the abbreviation
    `BW0ZON` instead of the HBV96 abbreviation `SM`.
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = hland_masks.Soil()

    CONTROLPARAMETERS = (hland_control.FC,)

    def trim(self, lower=None, upper=None):
        r"""Trim |SM| following :math:`0 \leq SM \leq FC`.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> fc(200.0)
        >>> states.sm(-100.0, 0.0, 100.0, 200.0, 300.0)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 200.0, 200.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.fc
        super().trim(lower, upper)


class UZ(sequencetools.StateSequence):
    """Storage in the upper zone layer [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)


class SUZ(sequencetools.StateSequence):
    """Upper storage reservoir [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class BW1(sequencetools.StateSequence):
    """Water stored in the surface flow reservoir [mm].

    Note that COSERO uses the abbreviation `BW1ZON` instead.
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = hland_masks.UpperZone()


class BW2(sequencetools.StateSequence):
    """Water stored in the interflow reservoir [mm].

    Note that COSERO uses the abbreviation `BW2ZON` instead.
    """

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = hland_masks.UpperZone()


class LZ(sequencetools.StateSequence):
    """Storage in the lower zone layer [mm].

    Note that COSERO uses the abbreviation `BW3Geb` instead of the HBV96 abbreviation
    `LZ`.
    """

    NDIM, NUMERIC, SPAN = 0, False, (None, None)

    CONTROLPARAMETERS = (hland_control.ZoneType,)

    def trim(self, lower=None, upper=None):
        """Trim negative values if the actual subbasin does not contain an internal
        lake.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(2)
        >>> zonetype(FIELD, ILAKE)
        >>> states.lz(-1.0)
        >>> states.lz
        lz(-1.0)
        >>> zonetype(FIELD, FOREST)
        >>> states.lz(-1.0)
        >>> states.lz
        lz(0.0)
        >>> states.lz(1.0)
        >>> states.lz
        lz(1.0)
        """
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            if not any(control.zonetype.values == ILAKE):
                lower = 0.0
        super().trim(lower, upper)


class SG1(sequencetools.StateSequence):
    """Fast response groundwater reservoir [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)

    CONTROLPARAMETERS = (hland_control.SG1Max,)
    mask = hland_masks.UpperZone()

    def trim(self, lower=None, upper=None):
        r"""Trim |SG1| following :math:`0  \leq SG1 \leq SG1Max`.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> sg1max(100.0)
        >>> states.sg1(-50.0, 0.0, 50.0, 100.0, 150.0)
        >>> states.sg1
        sg1(0.0, 0.0, 50.0, 100.0, 100.0)
        """
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.sg1max
        super().trim(lower, upper)


class SG2(sequencetools.StateSequence):
    """First-order slow response groundwater reservoir [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class SG3(sequencetools.StateSequence):
    """Second-order slow response groundwater reservoir [mm]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class SC(sequencetools.StateSequence):
    """Storage cascade for runoff concentration [mm]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
