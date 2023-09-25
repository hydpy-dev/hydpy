"""This module defines submodel interfaces for calculating potential
evapotranspiration."""
# import...
# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class PETModel_V1(modeltools.SubmodelInterface):
    """Simple interface for calculating all potential evapotranspiration values in one
    step."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |PETModel_V1| submodels."""

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
