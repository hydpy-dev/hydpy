# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.core import parametertools


class ZipParameter1D(parametertools.ZipParameter):
    """Base class for 1-dimensional parameters that provide additional keyword-based
    zipping functionalities."""

    constants = {}
    mask = masktools.SubmodelIndexMask()
