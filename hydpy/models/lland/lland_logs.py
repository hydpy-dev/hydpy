# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core import variabletools


# due to a pylint bug (see https://github.com/PyCQA/pylint/issues/870)
class WET0(sequencetools.LogSequence):
    """Zeitlich gewichtete Grasreferenzverdunstung (temporally weighted
    reference evapotranspiration) [mm]."""
    NDIM, NUMERIC = 2, False

    @variabletools.Variable.shape.setter   # pylint: disable=no-member
    def shape(self, shape):
        """Log sequence |WET0| is generally initialized with a length of one
        on the first axis:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> logs.wet0.shape = 3
        >>> logs.wet0.shape
        (1, 3)
        """
        # pylint: disable=no-member
        variabletools.Variable.shape.fset(self, (1, shape))

    shape.__doc__ = shape.fset.__doc__


class LogSequences(sequencetools.LogSequences):
    """Log sequences of the HydPy-L-Land model."""
    CLASSES = (WET0,)
