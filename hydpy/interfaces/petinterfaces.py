"""This module defines submodel interfaces for calculating potential
evapotranspiration."""
# import...
# ...from standard library
import abc

# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class PETModel_V1(modeltools.SubmodelInterface):
    """Simple interface for calculating all potential evapotranspiration values in one
    step."""

    typeid: ClassVar[Literal[1]] = 1

    @abc.abstractmethod
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place."""

    @abc.abstractmethod
    def prepare_zonetypes(self, zonetypes: Sequence[int]) -> None:
        """Set the types (usually land cover types) of the individual zones."""

    @abc.abstractmethod
    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km²."""

    @abc.abstractmethod
    def prepare_elevations(self, elevations: Sequence[float]) -> None:
        """Set the elevations of the individual zones in m."""

    @modeltools.abstractmodelmethod
    def determine_potentialevapotranspiration(self) -> None:
        """Calculate potential evapotranspiration."""

    @modeltools.abstractmodelmethod
    def get_potentialevapotranspiration(self, k: int) -> float:
        """Get the previously calculated potential evapotranspiration of the selected
        zone in mm/T."""

    @modeltools.abstractmodelmethod
    def get_meanpotentialevapotranspiration(self) -> float:
        """Get the previously calculated average potential evapotranspiration in
        mm/T."""
