"""This module defines submodel interfaces for calculating snow processes."""

import abc

from hydpy.core import modeltools
from hydpy.core.typingtools import *


class SnowModel_V1(modeltools.SubmodelInterface):
    """Interface for calculating the snowpack's water release and coverage degree."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |SnowModel_V1| submodels."""

    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place."""

    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km²."""

    def prepare_elevations(self, zoneheights: Sequence[float]) -> None:
        """Set the elevations of the individual zones in m."""

    def prepare_land(self, land: VectorInputBool) -> None:
        """Set flags indicating whether the individual zones represent land areas."""

    @abc.abstractmethod
    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Get the snowpack's "water balance delta" in mm.

        The "water balance delta" might be just the difference between the total water
        equivalent currently stored and that given in the initial conditions
        dictionary, but it may also include additional losses or gains, such as snow
        evaporation.
        """

    @modeltools.abstractmodelmethod
    def process_snowroutine(self) -> None:
        """Process the complete snow routine."""

    @modeltools.abstractmodelmethod
    def get_release(self, k: int) -> float:
        """Get the release of melted snow water or, if no snow layer exists,
        throughfall in mm/T."""

    @modeltools.abstractmodelmethod
    def get_snowcover(self, k: int) -> float:
        """Get the relative snow cover degree."""
