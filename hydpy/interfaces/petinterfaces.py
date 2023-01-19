"""This module defines submodel interfaces for calculating potential
evapotranspiration."""
# import...
# ...from standard library
from abc import abstractmethod
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

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
        """Get the previously calculated potential evapotranspiration in mm/T."""
