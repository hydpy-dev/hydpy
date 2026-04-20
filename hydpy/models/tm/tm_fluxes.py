# pylint: disable=missing-module-docstring

from hydpy.models.tm import tm_sequences


class PNet(tm_sequences.FluxSequence0D):
    """Net precipitation [mm/T]."""


class Perc(tm_sequences.FluxSequence0D):
    """Percolation [mm/T]."""


class QD(tm_sequences.FluxSequence0D):
    """Direct runoff [mm/T]."""


class QI(tm_sequences.FluxSequence0D):
    """Interflow [mm/T]."""


class QB(tm_sequences.FluxSequence0D):
    """Baseflow [mm/T]."""


class QT(tm_sequences.FluxSequence0D):
    """Total runoff [mm/T]."""
