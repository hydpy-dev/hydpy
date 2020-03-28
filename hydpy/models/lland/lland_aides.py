# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SN_Ratio(sequencetools.AideSequence):
    """Ratio of frozen precipitation to total precipitation [-]."""
    NDIM, NUMERIC = 1, False


class TempS(sequencetools.AideSequence):
    """Temperatur der Schneedecke (temperature of the snow layer) [°C].

    Note that the value of sequence |TempS| is |numpy.nan| for snow-free
    surfaces.
    """
    NDIM, NUMERIC = 1, False


class DailyGlobalRadiation(sequencetools.AideSequence):
    """ToDo Daily global Radiation [MJ/m²]."""
    NDIM, NUMERIC = 0, False
