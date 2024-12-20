# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Inputs(sequencetools.FluxSequence):
    """The (unmodified) values supplied by the input nodes [?]."""

    NDIM, NUMERIC = 1, False


class ActualConstant(sequencetools.FluxSequence):
    """The actual value for the constant of the linear regression model [?]."""

    NDIM, NUMERIC = 0, False


class ActualFactor(sequencetools.FluxSequence):
    """The actual value for the factor of the linear regression model [?]."""

    NDIM, NUMERIC = 0, False


class InputPredictions(sequencetools.FluxSequence):
    """The values of the input nodes predicted by a regression model [?]."""

    NDIM, NUMERIC = 1, False


class OutputPredictions(sequencetools.FluxSequence):
    """The values of the output nodes predicted by a regression model [?]."""

    NDIM, NUMERIC = 1, False


class InputResiduals(sequencetools.FluxSequence):
    """The exact residuals of a regression model calculated for the input nodes [?]."""

    NDIM, NUMERIC = 1, False


class OutputResiduals(sequencetools.FluxSequence):
    """The guessed residuals of a regression model interpolated for the input nodes
    [?]."""

    NDIM, NUMERIC = 1, False


class Outputs(sequencetools.FluxSequence):
    """The final interpolation results estimated for the output nodes [?]."""

    NDIM, NUMERIC = 1, False
