# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.whmod import whmod_sequences


class Interzeptionsspeicher(whmod_sequences.State1DSequence):
    """[mm]"""


class Schneespeicher(whmod_sequences.State1DSequence):
    """[mm]"""


class AktBodenwassergehalt(whmod_sequences.State1DSequence):
    """[mm]"""


class Zwischenspeicher(sequencetools.StateSequence):
    """[mm]"""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)
