# pylint: disable=missing-module-docstring

import numpy

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.hland import hland_control
from hydpy.models.hland import hland_masks
from hydpy.models.hland import hland_sequences
from hydpy.models.hland.hland_constants import ILAKE


class Ic(hland_sequences.State1DSequence):
    """Interception storage [mm]."""

    SPAN = (0.0, None)
    mask = hland_masks.Interception()


class SM(hland_sequences.State1DSequence):
    """Soil moisture [mm].

    Note that PREVAH uses the abbreviation `SSM`, and COSERO uses the abbreviation
    `BW0ZON` instead of the HBV96 abbreviation `SM`.
    """

    SPAN = (0.0, None)
    mask = hland_masks.Soil()

    CONTROLPARAMETERS = (hland_control.FC,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
            upper = self.subseqs.seqs.model.parameters.control.fc.values
        return super().trim(lower, upper)


class UZ(sequencetools.StateSequence):
    """Storage in the upper zone layer [mm]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)


class SUZ(hland_sequences.State1DSequence):
    """Upper storage reservoir [mm]."""

    SPAN = (0.0, None)


class BW1(hland_sequences.State1DSequence):
    """Water stored in the surface flow reservoir [mm].

    Note that COSERO uses the abbreviation `BW1ZON` instead.
    """

    SPAN = (0.0, None)
    mask = hland_masks.UpperZone()


class BW2(hland_sequences.State1DSequence):
    """Water stored in the interflow reservoir [mm].

    Note that COSERO uses the abbreviation `BW2ZON` instead.
    """

    SPAN = (0.0, None)
    mask = hland_masks.UpperZone()


class LZ(sequencetools.StateSequence):
    """Storage in the lower zone layer [mm].

    Note that COSERO uses the abbreviation `BW3Geb` instead of the HBV96 abbreviation
    `LZ`.
    """

    NDIM: Final[Literal[0]] = 0

    CONTROLPARAMETERS = (hland_control.ZoneType,)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
        return super().trim(lower, upper)


class SG1(hland_sequences.State1DSequence):
    """Fast response groundwater reservoir [mm]."""

    SPAN = (0.0, None)

    CONTROLPARAMETERS = (hland_control.SG1Max,)
    mask = hland_masks.UpperZone()

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
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
            upper = self.subseqs.seqs.model.parameters.control.sg1max.values
        return super().trim(lower, upper)


class SG2(sequencetools.StateSequence):
    """First-order slow response groundwater reservoir [mm]."""

    NDIM: Final[Literal[0]] = 0


class SG3(sequencetools.StateSequence):
    """Second-order slow response groundwater reservoir [mm]."""

    NDIM: Final[Literal[0]] = 0


class SC(sequencetools.StateSequence):
    """Storage cascade for runoff concentration [mm]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)
