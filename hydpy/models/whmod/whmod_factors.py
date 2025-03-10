# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from hland
from hydpy.models.whmod import whmod_sequences


class RelativeSoilMoisture(whmod_sequences.Factor1DSoilSequence):
    """Crop-available relative soil water content [-]."""
