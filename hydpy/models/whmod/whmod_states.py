# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Interzeptionsspeicher(sequencetools.StateSequence):
    NDIM, NUMERIC, SPAN = 1, False, (0., None)
    """[mm]"""


class Schneespeicher(sequencetools.StateSequence):
    """[mm]"""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class AktBodenwassergehalt(sequencetools.StateSequence):
    """[mm]"""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class Zwischenspeicher(sequencetools.StateSequence):
    """[mm]"""
    NDIM, NUMERIC, SPAN = 0, False, (None, None)
