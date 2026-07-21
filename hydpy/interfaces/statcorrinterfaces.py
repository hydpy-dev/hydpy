"""This module defines submodel interfaces for statistical output correction of
discharge forecasts."""

from hydpy.core import modeltools
from hydpy.core.typingtools import *


class OutputCorrModel_V1(modeltools.SubmodelInterface):
    """Simple interface for statistical output correction of discharge forecasts.

    Each submodel owns and maintains its own persistent log of simulated and
    observed discharge.  The main model (|statcorr|) merely passes the current
    simulated and observed discharge to the submodel once per simulation step;
    the submodel is responsible for shifting these values into its internal log
    and for using the resulting history when calculating the correction.

    The expected call order within one simulation step is:

    1. |OutputCorrModel_V1.set_simulateddischarge|
    2. |OutputCorrModel_V1.set_observeddischarge|
    3. |OutputCorrModel_V1.determine_outputcorrection|
    4. |OutputCorrModel_V1.get_correctedoutput|
    """

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |OutputCorrModel_V1| submodels."""

    def prepare_nmblogentries(self, nmblogentries: int) -> None:
        """Allocate the internal log to hold `nmblogentries` discharge values."""

    @modeltools.abstractmodelmethod
    def set_simulateddischarge(self, simulateddischarge: float) -> None:
        """Pass the current simulated discharge (in m³/s) to the submodel, which
        appends it to its internal log of simulated discharge."""

    @modeltools.abstractmodelmethod
    def set_observeddischarge(self, observeddischarge: float) -> None:
        """Pass the current observed discharge (in m³/s, or |numpy.nan| when
        unavailable) to the submodel, which appends it to its internal log of
        observed discharge."""

    @modeltools.abstractmodelmethod
    def determine_outputcorrection(self, isforecastmode: bool) -> None:
        """Calculate the corrected output discharge from the internal logs of
        simulated and observed discharge.

        The main model passes its current |Options.simulationmode| via
        `isforecastmode` (|True| for `forecast`, |False| for `historical`)
        instead of leaving the submodel to inspect the global option itself,
        because a submodel cannot safely track *changes* of
        |Options.simulationmode| between simulation steps on its own (there is
        no per-step hook comparable to |OutputCorrModel_V1.set_simulateddischarge|
        for it, and refreshing a submodel-owned derived parameter via
        |Model.update_parameters| would also needlessly re-run its submodel
        attachment/initialisation logic, wiping its logged history)."""

    @modeltools.abstractmodelmethod
    def get_correctedoutput(self) -> float:
        """Get the previously calculated corrected discharge in m³/s."""
