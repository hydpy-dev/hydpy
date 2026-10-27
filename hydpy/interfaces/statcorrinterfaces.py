"""This module defines submodel interfaces for the statistical output correction of
simulated values (for example, discharge forecasts) based on observed values."""

from hydpy.core import modeltools
from hydpy.core.typingtools import *


class OutputCorrModel_V1(modeltools.SubmodelInterface):
    """Simple interface for the statistical output correction of simulated values.

    The interface does not prescribe the corrected variable (|statcorr_main|, for
    example, corrects discharge).  All values passed to and returned by the
    submodel share the unit of this variable.

    Each submodel owns and maintains its own persistent log of simulated and
    observed values.  The main model merely passes the current simulated and
    observed value to the submodel once per simulation step;
    the submodel is responsible for shifting these values into its internal log
    and for using the resulting history when calculating the correction.  It also
    determines the required length of its log from its own parameters.

    The expected call order within one simulation step is:

    1. |OutputCorrModel_V1.set_simulatedvalue|
    2. |OutputCorrModel_V1.set_observedvalue|
    3. |OutputCorrModel_V1.determine_outputcorrection|
    4. |OutputCorrModel_V1.is_active|
    5. |OutputCorrModel_V1.get_correctedoutput|
    """

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |OutputCorrModel_V1| submodels."""

    @modeltools.abstractmodelmethod
    def set_simulatedvalue(self, simulatedvalue: float) -> None:
        """Pass the current simulated value to the submodel, which appends it to
        its internal log of simulated values."""

    @modeltools.abstractmodelmethod
    def set_observedvalue(self, observedvalue: float) -> None:
        """Pass the current observed value (or |numpy.nan| when unavailable) to the
        submodel, which appends it to its internal log of observed values."""

    @modeltools.abstractmodelmethod
    def determine_outputcorrection(self, isforecastmode: bool) -> None:
        """Calculate the corrected output value from the internal logs of
        simulated and observed values.

        The main model passes its current |Options.simulationmode| via
        `isforecastmode` (|True| for `forecast`, |False| for `historical`)
        instead of leaving the submodel to inspect the global option itself,
        because a submodel cannot safely track *changes* of
        |Options.simulationmode| between simulation steps on its own (there is
        no per-step hook comparable to |OutputCorrModel_V1.set_simulatedvalue|
        for it, and refreshing a submodel-owned derived parameter via
        |Model.update_parameters| would also needlessly re-run its submodel
        attachment/initialisation logic, wiping its logged history)."""

    @modeltools.abstractmodelmethod
    def is_active(self) -> bool:
        """Tell whether the submodel was responsible for correcting the simulated
        value during the most recent call of
        |OutputCorrModel_V1.determine_outputcorrection|."""

    @modeltools.abstractmodelmethod
    def get_correctedoutput(self) -> float:
        """Get the previously calculated corrected value."""
