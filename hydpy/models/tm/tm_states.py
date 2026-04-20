# pylint: disable=missing-module-docstring

from hydpy.models.tm import tm_sequences


class S(tm_sequences.StateSequence0D):
    """Upper layer (soil) storage [mm]."""

    SPAN = (0.0, None)


class G(tm_sequences.StateSequence0D):
    """Lower layer (groundwater) storage [mm]."""

    SPAN = (0.0, None)
