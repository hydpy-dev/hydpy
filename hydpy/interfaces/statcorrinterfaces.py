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
        """Set the simulated value."""

    @modeltools.abstractmodelmethod
    def set_observedvalue(self, observedvalue: float) -> None:
        """Set the observed value."""

    @modeltools.abstractmodelmethod
    def determine_outputcorrection(self) -> None:
        """Calculate the corrected output value."""

    @modeltools.abstractmodelmethod
    def is_active(self) -> bool:
        """Tell whether |OutputCorrModel_V1.determine_outputcorrection|
        succeeded.
        """

    @modeltools.abstractmodelmethod
    def get_correctedoutput(self) -> float:
        """Get the previously calculated corrected value (which can be
        the originally simulated value, if the output correction is not active).
        """
