# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.framework import sequencetools
from hydpy.models.hland.hland_constants import ILAKE


class Ic(sequencetools.StateSequence):
    """Interception storage [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`IC \\leq ICMAX`."""
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            upper = control.icmax
        sequencetools.StateSequence.trim(self, lower, upper)

class SP(sequencetools.StateSequence):
    """Frozen water stored in the snow layer [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class WC(sequencetools.StateSequence):
    """Liquid water content of the snow layer [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`WC \\leq WHC \\cdot SP`."""
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            states = self.subseqs
            upper = control.whc*states.sp
        sequencetools.StateSequence.trim(self, lower, upper)

class SM(sequencetools.StateSequence):
    """Soil moisture [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`SM \\leq FC`."""
        if upper is None:
            upper = self.subseqs.seqs.model.parameters.control.fc
        sequencetools.StateSequence.trim(self, lower, upper)

class UZ(sequencetools.StateSequence):
    """Storage in the upper zone layer [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class LZ(sequencetools.StateSequence):
    """Storage in the lower zone layer [mm]."""
    NDIM, NUMERIC, SPAN = 0, False, (None, None)

    def trim(self, lower=None, upper=None):
        """Trim negative value whenever there is no internal lake within
        the respective subbasin.
        """
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            if not any(control.zonetype==ILAKE):
                lower = 0.
        sequencetools.StateSequence.trim(self, lower, upper)

class StateSequences(sequencetools.StateSequences):
    """State sequences of the hland model."""
    _SEQCLASSES = (Ic, SP, WC, SM, UZ, LZ)

