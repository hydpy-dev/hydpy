# pylint: disable=missing-module-docstring

from hydpy.models.snow import snow_sequences


class IceContentExcess(snow_sequences.AideSequence1D):
    """Subbasin-internal redistribution excess of the snow's ice content [mm/T]."""


class WaterContentExcess(snow_sequences.AideSequence1D):
    """Subbasin-internal redistribution excess of the snow's water content [mm/T]."""
