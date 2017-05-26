# -*- coding: utf-8 -*-

# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools

class Model(modeltools.Model):
    """Base model for HydPy-L-Lake."""

    _RUNMETHODS = ()
