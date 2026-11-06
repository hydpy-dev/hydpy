# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.conv import conv_variables


class Inputs(conv_variables.MixinInputs, sequencetools.FluxSequence):
    """The (unmodified) values supplied by the input nodes [?]."""

    NDIM: Final[Literal[1]] = 1


class ActualConstant(sequencetools.FluxSequence):
    """The actual value for the constant of the linear regression model [?]."""

    NDIM: Final[Literal[0]] = 0


class ActualFactor(sequencetools.FluxSequence):
    """The actual value for the factor of the linear regression model [?]."""

    NDIM: Final[Literal[0]] = 0


class InputPredictions(conv_variables.MixinInputs, sequencetools.FluxSequence):
    """The values of the input nodes predicted by a regression model [?]."""

    NDIM: Final[Literal[1]] = 1


class OutputPredictions(conv_variables.MixinOutputs, sequencetools.FluxSequence):
    """The values of the output nodes predicted by a regression model [?]."""

    NDIM: Final[Literal[1]] = 1


class InputResiduals(conv_variables.MixinInputs, sequencetools.FluxSequence):
    """The exact residuals of a regression model calculated for the input nodes [?]."""

    NDIM: Final[Literal[1]] = 1


class OutputResiduals(conv_variables.MixinOutputs, sequencetools.FluxSequence):
    """The guessed residuals of a regression model interpolated for the input nodes
    [?]."""

    NDIM: Final[Literal[1]] = 1


class CurrentInputAverages(conv_variables.MixinInputs, sequencetools.FluxSequence):
    """The long-term averages of the input nodes for the current month [?]."""

    NDIM: Final[Literal[1]] = 1


class CurrentOutputAverages(conv_variables.MixinOutputs, sequencetools.FluxSequence):
    """The long-term averages of the output nodes for the current month [?]."""

    NDIM: Final[Literal[1]] = 1


class InputRatios(conv_variables.MixinInputs, sequencetools.FluxSequence):
    """The ratios between the current values supplied by the input nodes and their
    long-term averages for the current month [-]."""

    NDIM: Final[Literal[1]] = 1


class OutputRatios(conv_variables.MixinOutputs, sequencetools.FluxSequence):
    """The ratios between the final results and the long-term averages for the current
    month, interpolated for the output nodes [-]."""

    NDIM: Final[Literal[1]] = 1


class Outputs(conv_variables.MixinOutputs, sequencetools.FluxSequence):
    """The final interpolation results estimated for the output nodes [?]."""

    NDIM: Final[Literal[1]] = 1
