# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from hland
from hydpy.models.whmod import whmod_sequences


class RelBodenfeuchte(whmod_sequences.Factor1DSequence):
    """[-]"""


class Saettigungsdampfdruckdefizit(sequencetools.FactorSequence):
    """[mbar]"""

    NDIM, NUMERIC = 0, False
