# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...HydPy specific
from hydpy.core import sequencetools
from hydpy.models.hland.hland_constants import ILAKE


class Ic(sequencetools.StateSequence):
    """Interception storage [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`IC \\leq ICMAX`.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(5)
        >>> icmax(2.)
        >>> states.ic(-1.,0., 1., 2., 3.)
        >>> states.ic
        ic(0.0, 0.0, 1.0, 2.0, 2.0)
        """
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            upper = control.icmax
        sequencetools.StateSequence.trim(self, lower, upper)


class SP(sequencetools.StateSequence):
    """Frozen water stored in the snow layer [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (None, None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`WC \\leq WHC \\cdot SP`.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(7)
        >>> whc(.1)
        >>> states.wc.values = -1., 0., 1., -1., 0., .5, 1.
        >>> states.sp(-1., 0., 0., 5., 5., 5., 5.)
        >>> states.sp
        sp(0.0, 0.0, 10.0, 5.0, 5.0, 5.0, 10.0)
        """
        whc = self.subseqs.seqs.model.parameters.control.whc
        wc = self.subseqs.wc
        if lower is None:
            if wc.values is not None:
                lower = numpy.clip(wc/whc, 0., numpy.inf)
            else:
                lower = 0.
        sequencetools.StateSequence.trim(self, lower, upper)


class WC(sequencetools.StateSequence):
    """Liquid water content of the snow layer [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`WC \\leq WHC \\cdot SP`.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(7)
        >>> whc(.1)
        >>> states.sp = 0., 0., 0., 5., 5., 5., 5.
        >>> states.wc(-1., 0., 1., -1., 0., .5, 1.)
        >>> states.wc
        wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5)
        """
        whc = self.subseqs.seqs.model.parameters.control.whc
        sp = self.subseqs.sp
        if (upper is None) and (sp.values is not None):
            upper = whc*sp
        sequencetools.StateSequence.trim(self, lower, upper)


class SM(sequencetools.StateSequence):
    """Soil moisture [mm]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`SM \\leq FC`.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(5)
        >>> fc(200.)
        >>> states.sm(-100.,0., 100., 200., 300.)
        >>> states.sm
        sm(0.0, 0.0, 100.0, 200.0, 200.0)
        """
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

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(2)
        >>> zonetype(FIELD, ILAKE)
        >>> states.lz(-1.)
        >>> states.lz
        lz(-1.0)
        >>> zonetype(FIELD, FOREST)
        >>> states.lz(-1.0)
        >>> states.lz
        lz(0.0)
        >>> states.lz(1.)
        >>> states.lz
        lz(1.0)
        """
        if upper is None:
            control = self.subseqs.seqs.model.parameters.control
            if not any(control.zonetype.values == ILAKE):
                lower = 0.
        sequencetools.StateSequence.trim(self, lower, upper)


class StateSequences(sequencetools.StateSequences):
    """State sequences of the HydPy-H-Land model."""
    _SEQCLASSES = (Ic, SP, WC, SM, UZ, LZ)
