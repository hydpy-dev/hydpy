# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Inputs(sequencetools.FluxSequence):
    """Inputs [?]."""

    NDIM, NUMERIC = 1, False


class Outputs(sequencetools.FluxSequence):
    """Outputs [?]."""

    NDIM, NUMERIC = 1, False
