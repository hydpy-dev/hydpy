# pylint: disable=missing-module-docstring

from hydpy.models.whmod import whmod_sequences


class RelativeSoilMoisture(whmod_sequences.Factor1DSoilSequence):
    """Crop-available relative soil water content [-]."""

    SPAN = (0.0, 1.0)
