# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class WBMin(parametertools.FixedParameter):
    """Mindestwert der Wasserspiegelbreite  (minimum value of the water level
    width [m].

    In theory, the value of |WBMin| should always be zero.  However, at least
    the numerical implementation of application model |lstream_v001| requires
    a value slightly lower than zero for reasons of numerical stability
    when the simulated river section is dry.
    """

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 1e-9


class WBReg(parametertools.FixedParameter):
    """Auf |WBMin| bezogener effektiver Glättungsparameter (effectiv smoothing
    parameter related to |WBMin|) [m]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 1e-5
