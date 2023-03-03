"""This module defines submodel interfaces for providing precipitation."""
# import...
# ...from standard library
import abc

# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class PrecipModel_V1(modeltools.SubmodelInterface):
    """Pure getter interface for using main models as sub-submodels."""

    typeid: ClassVar[Literal[1]] = 1

    @modeltools.abstractmodelmethod
    def get_precipitation(self, k: int) -> float:
        """Get the selected zone's precipitation value in mm/T."""


class PrecipModel_V2(modeltools.SubmodelInterface):
    """Simple interface for determining precipitation in one step."""

    typeid: ClassVar[Literal[2]] = 2

    @abc.abstractmethod
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place."""

    @abc.abstractmethod
    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km²."""

    @modeltools.abstractmodelmethod
    def determine_precipitation(self) -> None:
        """Determine precipitation."""

    @modeltools.abstractmodelmethod
    def get_precipitation(self, k: int) -> float:
        """Get the selected zone's precipitation value in mm/T."""

    @modeltools.abstractmodelmethod
    def get_meanprecipitation(self) -> float:
        """Get the previously calculated average precipitation in mm/T."""
