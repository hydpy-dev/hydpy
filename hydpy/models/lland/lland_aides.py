# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class EPW(sequencetools.AideSequence):
    """Potenzielle Evaporation/Evapotranspiration von Wasserflächen (potential
    evaporation/evapotranspiration combined from all water areas) [mm]."""
    NDIM, NUMERIC = 0, False


class K(sequencetools.AideSequence):
    """Float to help nhru iterating for Pegasus"""
    NDIM, NUMERIC = 0, False


class SN_Ratio(sequencetools.AideSequence):
    """Ratio of frozen precipitation to total precipitation [-]."""
    NDIM, NUMERIC = 1, False


class TempS(sequencetools.AideSequence):
    """Temperatur der Schneedecke (temperature of the snow layer) [°C].

    Gibt es keinen Schnee (|WAeS|=0), so wird die Schneetemperatur auf NaN
    gesetzt (If there is no snow (|WAeS|=0), snow the temperature is set to
    NaN).

    """
    NDIM, NUMERIC = 1, False
