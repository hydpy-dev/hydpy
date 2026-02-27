# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class Inputs(sequencetools.FluxSequence):
    """The (unmodified) values supplied by the input nodes [?]."""

    NDIM: Final[Literal[1]] = 1


class ActualConstant(sequencetools.FluxSequence):
    """The actual value for the constant of the linear regression model [?]."""

    NDIM: Final[Literal[0]] = 0


class ActualFactor(sequencetools.FluxSequence):
    """The actual value for the factor of the linear regression model [?]."""

    NDIM: Final[Literal[0]] = 0


class InputPredictions(sequencetools.FluxSequence):
    """The values of the input nodes predicted by a regression model [?]."""

    NDIM: Final[Literal[1]] = 1


class OutputPredictions(sequencetools.FluxSequence):
    """The values of the output nodes predicted by a regression model [?]."""

    NDIM: Final[Literal[1]] = 1


class InputResiduals(sequencetools.FluxSequence):
    """The exact residuals of a regression model calculated for the input nodes [?]."""

    NDIM: Final[Literal[1]] = 1


class OutputResiduals(sequencetools.FluxSequence):
    """The guessed residuals of a regression model interpolated for the input nodes
    [?]."""

    NDIM: Final[Literal[1]] = 1


class Outputs(sequencetools.FluxSequence):
    """The final interpolation results estimated for the output nodes [?]."""

    NDIM: Final[Literal[1]] = 1
