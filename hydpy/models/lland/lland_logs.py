# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools


class WET0(sequencetools.LogSequence):
    """Zeitlich gewichtete Grasreferenzverdunstung (temporally weighted
    reference evapotranspiration) [mm]."""
    NDIM, NUMERIC = 2, False

    def __hydpy__get_shape__(self):
        """Log sequence |WET0| is generally initialized with a length of one
        on the first axis:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> logs.wet0.shape = 3
        >>> logs.wet0.shape
        (1, 3)
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape):
        super().__hydpy__set_shape__((1, shape))

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of the HydPy-L-Land model."""
    CLASSES = (WET0,)
