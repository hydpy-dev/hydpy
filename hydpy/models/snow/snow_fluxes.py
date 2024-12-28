# pylint: disable=missing-module-docstring

# ...from snow
from hydpy.models.snow import snow_sequences


class PLayer(snow_sequences.Flux1DSequence):
    """Precipitation of each snow layer[mm]."""

    NDIM, NUMERIC = 1, False


class PSnowLayer(snow_sequences.Flux1DSequence):
    """Snowfall of each snow layer[mm]."""

    NDIM, NUMERIC = 1, False


class PRainLayer(snow_sequences.Flux1DSequence):
    """Rainfall of each snow layer[mm]."""

    NDIM, NUMERIC = 1, False


class TLayer(snow_sequences.Flux1DSequence):
    """Daily mean air temperature of each snow layer [°C]."""

    NDIM, NUMERIC = 1, False


class TMinLayer(snow_sequences.Flux1DSequence):
    """Daily minimum air temperature of each snow layer [°C]."""

    NDIM, NUMERIC = 1, False


class TMaxLayer(snow_sequences.Flux1DSequence):
    """Daily maximum air temperature of each snow layer [°C]."""

    NDIM, NUMERIC = 1, False


class SolidFraction(snow_sequences.Flux1DSequence):
    # todo solidfractionprecipitation
    """Solid Fraction of precipitation [/]."""

    NDIM, NUMERIC, SPAN = 1, False, (0, 1)


class PotMelt(snow_sequences.Flux1DSequence):
    """Potential snow melt [mm]."""

    NDIM, NUMERIC = 1, False


class Melt(snow_sequences.Flux1DSequence):
    """Snow melt [mm]."""

    NDIM, NUMERIC = 1, False


class PNetLayer(snow_sequences.Flux1DSequence):
    """Net Precipitation of each snow layer [mm]."""

    NDIM, NUMERIC = 1, False


class PNet(snow_sequences.Flux1DSequence):
    """Net Precipitation of catchment [mm]."""

    NDIM, NUMERIC = 0, False
