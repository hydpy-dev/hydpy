# pylint: disable=missing-module-docstring

from hydpy.models.snow import snow_sequences


class GLocalMax(snow_sequences.Log1DNLayers):
    """Local melt threshold [mm]."""
