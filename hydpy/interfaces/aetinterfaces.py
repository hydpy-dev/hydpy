"""This module defines submodel interfaces for calculating actual evapotranspiration."""
# import...
# ...from standard library
import abc

# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class AETModel_V1(modeltools.SubmodelInterface):
    """Interface for calculating actual evapotranspiration values in one
    step."""

    typeid: ClassVar[Literal[1]] = 1

    @abc.abstractmethod
    def prepare_water(self, water: VectorInputBool) -> None:
        """Set the flags for whether the individual zones are water areas or not."""

    @abc.abstractmethod
    def prepare_interception(self, interception: VectorInputBool) -> None:
        """Set the flags for whether interception evaporation is relevant for the
        individual zones."""

    @abc.abstractmethod
    def prepare_soil(self, soil: VectorInputBool) -> None:
        """Set the flags for whether soil evapotranspiration is relevant for the
        individual zones."""

    @abc.abstractmethod
    def prepare_maxsoilwater(self, maxsoilwater: VectorInputFloat) -> None:
        """Set the maximum soil water content."""

    @modeltools.abstractmodelmethod
    def determine_interceptionevaporation(self) -> None:
        """Determine the actual interception evaporation."""

    @modeltools.abstractmodelmethod
    def determine_soilevapotranspiration(self) -> None:
        """Determine the actual evapotranspiration from the soil."""

    @modeltools.abstractmodelmethod
    def determine_waterevaporation(self) -> None:
        """Determine the actual evapotranspiration from open water areas."""

    @modeltools.abstractmodelmethod
    def get_interceptionevaporation(self, k: int) -> float:
        """Get the selected zone's previously calculated interception evaporation in
        mm/T."""

    @modeltools.abstractmodelmethod
    def get_soilevapotranspiration(self, k: int) -> float:
        """Get the selected zone's previously calculated soil evapotranspiration in
        mm/T."""

    @modeltools.abstractmodelmethod
    def get_waterevaporation(self, k: int) -> float:
        """Get the selected zone's previously calculated water area evaporation in
        mm/T."""
