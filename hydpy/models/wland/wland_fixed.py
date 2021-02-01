# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class Pi(parametertools.FixedParameter):
    """π [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 3.141592653589793
