"""This module defines submodel interfaces for calculating runoff concentration
processes."""

# import...
# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class RConcModel_V1(modeltools.SubmodelInterface):
    """Interface for calculating the unit hydrograph or linear storage cascade
    output."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |RConcModel_V1| submodels."""

    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Get the water balance."""

    @modeltools.abstractmodelmethod
    def set_inflow(self, v: float) -> None:
        """Set the runoff concentration input."""

    @modeltools.abstractmodelmethod
    def determine_outflow(self) -> None:
        """Calculate runoff concentration output."""

    @modeltools.abstractmodelmethod
    def get_outflow(self) -> float:
        """Get the previously calculated runoff concentration output."""
