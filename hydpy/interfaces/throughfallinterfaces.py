"""This module defines submodel interfaces for providing throughfall."""

from hydpy.core import modeltools
from hydpy.core.typingtools import *


class ThroughfallModel_V1(modeltools.SubmodelInterface):
    """Pure getter interface for using main models as sub-submodels."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |ThroughfallModel_V1| submodels."""

    @modeltools.abstractmodelmethod
    def get_throughfall(self, k: int) -> float:
        """Get the selected zone's throughfall value in mm/T."""


class ThroughfallModel_V2(modeltools.SubmodelInterface):
    """Simple interface for determining throughfall in one step."""

    typeid: ClassVar[Literal[2]] = 2
    """Type identifier for |ThroughfallModel_V2| submodels."""

    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place."""

    @modeltools.abstractmodelmethod
    def determine_throughfall(self) -> None:
        """Determine throughfall."""

    @modeltools.abstractmodelmethod
    def get_throughfall(self, k: int) -> float:
        """Get the selected zone's throughfall value in mm/T."""
