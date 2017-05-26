# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools



class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-L-Lake, directly defined by the user."""
    _PARCLASSES = ()