"""This module defines submodel interfaces for providing precipitation."""
# import...
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

    @modeltools.abstractmodelmethod
    def determine_precipitation(self) -> None:
        """Determine precipitation."""

    @modeltools.abstractmodelmethod
    def get_precipitation(self, k: int) -> float:
        """Get the selected zone's precipitation value in mm/T."""

    @modeltools.abstractmodelmethod
    def get_meanprecipitation(self) -> float:
        """Get the previously calculated average precipitation in mm/T."""
