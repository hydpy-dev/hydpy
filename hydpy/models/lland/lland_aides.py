# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SNRatio(sequencetools.AideSequence):
    """Ratio of frozen precipitation to total precipitation [-]."""

    NDIM, NUMERIC = 1, False


class RLAtm(sequencetools.AideSequence):
    """Atmosphärische Gegenstrahlung (longwave radiation emitted from the
    atmosphere) [MJ/m²/d]."""

    NDIM, NUMERIC = 1, False


class TempS(sequencetools.AideSequence):
    """Temperatur der Schneedecke (temperature of the snow layer) [°C].

    Note that the value of sequence |TempS| is |numpy.nan| for snow-free
    surfaces.
    """

    NDIM, NUMERIC = 1, False
