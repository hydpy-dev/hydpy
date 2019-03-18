# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Niederschlag(sequencetools.InputSequence):
    """[mm/T]"""
    NDIM, NUMERIC = 0, False


class Temp_TM(sequencetools.InputSequence):
    """[°C]"""
    NDIM, NUMERIC = 0, False


class Temp14(sequencetools.InputSequence):
    """[°C]"""
    NDIM, NUMERIC = 0, False


class RelLuftfeuchte(sequencetools.InputSequence):
    """[-]"""
    NDIM, NUMERIC = 0, False


class InputSequences(sequencetools.InputSequences):
    CLASSES = (Niederschlag,
               Temp_TM,
               Temp14,
               RelLuftfeuchte)
