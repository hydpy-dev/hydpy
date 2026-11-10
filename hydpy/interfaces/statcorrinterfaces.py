"""This module defines submodel interfaces for the statistical output correction of
simulated values (for example, discharge forecasts) based on observed values."""

from hydpy.core import modeltools
from hydpy.core.typingtools import *


class OutputCorrModel_V1(modeltools.SubmodelInterface):
    """Simple interface for the statistical output correction of simulated values."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |OutputCorrModel_V1| submodels."""

    @modeltools.abstractmodelmethod
    def set_simulatedvalue(self, simulatedvalue: float) -> None:
        """Pass the current simulated value to the submodel."""

    @modeltools.abstractmodelmethod
    def set_observedvalue(self, observedvalue: float) -> None:
        """Pass the current observed value (or |numpy.nan| when unavailable) to the
        submodel."""

    @modeltools.abstractmodelmethod
    def determine_outputcorrection(self) -> None:
        """Calculate the corrected output value from the internal logs of
        simulated and observed values."""

    @modeltools.abstractmodelmethod
    def is_active(self) -> bool:
        """Tell whether the submodel was responsible for correcting the simulated
        value during the most recent call of
        |OutputCorrModel_V1.determine_outputcorrection|."""

    @modeltools.abstractmodelmethod
    def get_correctedoutput(self) -> float:
        """Get the previously calculated corrected value."""
