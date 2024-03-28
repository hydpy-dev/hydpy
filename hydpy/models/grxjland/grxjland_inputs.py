# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """Net Precipitation [mm]."""

    NDIM, NUMERIC = 0, False
