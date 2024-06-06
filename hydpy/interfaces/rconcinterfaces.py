"""This module defines submodel interfaces for calculating runoff concentration
processes."""

# import...
# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class RConcModel_V1(modeltools.SubmodelInterface):
    """Simple interface for calculating runoff concentration processes."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |RConcModel_V1| submodels."""

    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Get the difference between currently stored water and the given initial
        conditions in mm."""

    @modeltools.abstractmodelmethod
    def set_inflow(self, inflow: float) -> None:
        """Set the runoff concentration input in mm/T."""

    @modeltools.abstractmodelmethod
    def determine_outflow(self) -> None:
        """Calculate runoff concentration output."""

    @modeltools.abstractmodelmethod
    def get_outflow(self) -> float:
        """Get the previously calculated runoff concentration output in mm/T."""
