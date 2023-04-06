# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class GradP(parametertools.FixedParameter):
    """Altitude gradient precipitation [todo/m]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 0.00041


class ZThreshold(parametertools.FixedParameter):
    """Mean Altitude threshold constant precipitation [m]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 4000
