"""This module defines submodel interfaces for providing temperature."""
# import...
# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class TempModel_V1(modeltools.SubmodelInterface):
    """Pure getter interface for using main models as sub-submodels."""

    typeid: ClassVar[Literal[1]] = 1

    @modeltools.abstractmodelmethod
    def get_temperature(self, k: int) -> float:
        """Get the selected zone's temperature value in °C."""

    @modeltools.abstractmodelmethod
    def get_meantemperature(self) -> float:
        """Get the basin's mean temperature value in °C."""


class TempModel_V2(modeltools.SubmodelInterface):
    """Simple interface for determining the temperature in one step."""

    typeid: ClassVar[Literal[2]] = 2

    @modeltools.abstractmodelmethod
    def determine_temperature(self) -> None:
        """Determine temperature."""

    @modeltools.abstractmodelmethod
    def get_temperature(self, k: int) -> float:
        """Get the selected zone's temperature value in °C."""

    @modeltools.abstractmodelmethod
    def get_meantemperature(self) -> float:
        """Get the previously calculated average temperature in °C."""
