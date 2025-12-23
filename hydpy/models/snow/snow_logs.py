# pylint: disable=missing-module-docstring

# import...
# ...from snow
from hydpy.models.snow import snow_sequences


class GLocalMax(snow_sequences.Log1DNLayers):
    """Local melt threshold [mm]."""
