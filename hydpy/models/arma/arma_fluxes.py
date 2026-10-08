# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.arma import arma_variables


class QIn(sequencetools.FluxSequence):
    """Total inflow [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)


class QPIn(arma_variables.MixinNmb, sequencetools.FluxSequence):
    """Inflow portions corresponding to the different thresholds [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QMA(arma_variables.MixinNmb, sequencetools.FluxSequence):
    """MA result for the different thresholds [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QAR(arma_variables.MixinNmb, sequencetools.FluxSequence):
    """AR result for the different thresholds [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QPOut(arma_variables.MixinNmb, sequencetools.FluxSequence):
    """Outflow portions corresponding to the different thresholds [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    SPAN = (0.0, None)


class QOut(sequencetools.FluxSequence):
    """Total outflow [m³/s]."""

    NDIM: Final[Literal[0]] = 0
    SPAN = (0.0, None)
