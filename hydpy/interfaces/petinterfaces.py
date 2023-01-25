"""This module defines submodel interfaces for calculating potential
evapotranspiration."""
# import...
# ...from standard library
from abc import abstractmethod
from typing import *

# ...from hydpy
from hydpy.core import modeltools


class PETModel_V1(modeltools.SubmodelInterface):
    """Simple interface for calculating all potential evapotranspiration values in one
    step."""

    typeid: ClassVar[Literal[1]] = 1

    @abstractmethod
    def determine_potentialevapotranspiration(self) -> None:
        """Calculate potential evapotranspiration."""

    @abstractmethod
    def get_potentialevapotranspiration(self, k: int) -> float:
        """Get the previously calculated potential evapotranspiration of the selected
        hydrological response unit in mm/T."""

    @abstractmethod
    def get_meanpotentialevapotranspiration(self) -> float:
        """Get the previously average calculated potential evapotranspiration in
        mm/T."""
