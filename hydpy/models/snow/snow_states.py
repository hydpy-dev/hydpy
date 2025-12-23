# pylint: disable=missing-module-docstring

# import...
# ...from snow
from hydpy.models.snow import snow_sequences


class G(snow_sequences.State1DNLayers):
    """Snow pack [mm]."""

    SPAN = (0.0, None)


class ETG(snow_sequences.State1DNLayers):
    """Thermal state of the snow pack [°C]."""

    SPAN = (None, 0.0)


class GRatio(snow_sequences.State1DNLayers):
    """Ratio of the snow-covered area [-]."""

    SPAN = (0.0, 1.0)
