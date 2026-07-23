# pylint: disable=missing-module-docstring

from hydpy.models.snow import snow_sequences


class SPE(snow_sequences.AideSequence1D):
    """Subbasin-internal redistribution excess of the snow's ice content [mm/T]."""


class WCE(snow_sequences.AideSequence1D):
    """Subbasin-internal redistribution excess of the snow's water content [mm/T]."""
