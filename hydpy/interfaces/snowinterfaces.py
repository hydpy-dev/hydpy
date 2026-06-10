"""ToDo"""

from hydpy.core import modeltools
from hydpy.core.typingtools import *


class SnowModel_V1(modeltools.SubmodelInterface):
    """ToDo"""

    typeid: ClassVar[Literal[1]] = 1
    """ToDo"""

    def prepare_nmbzones(self, nmbzones: int) -> None:
        """ToDo"""

    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km²."""

    def prepare_water(self, water: VectorInputBool) -> None:
        """Set the flags for whether the individual zones are water areas or not."""

    # ToDo: abstrakte Methode?
    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Get the difference between currently stored water and the given initial
        conditions in mm."""

    @modeltools.abstractmodelmethod
    def determine_release(self) -> None:
        """ToDo"""

    @modeltools.abstractmodelmethod
    def get_release(self, k: int) -> float:
        """ToDo"""

