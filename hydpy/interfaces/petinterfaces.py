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

    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place."""

    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km²."""

    def prepare_zonetypes(self, zonetypes: Sequence[int]) -> None:
        """Set the types (usually land cover types) of the individual zones."""

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


class PETModel_V2(modeltools.SubmodelInterface):
    """Interface for calculating separate potential interception, soil, and water
    evapotranspiration values.

    An essential note for model developers: All main models using the |PETModel_V2|
    interface must first call |PETModel_V2.determine_potentialinterceptionevaporation|
    but are free to choose the execution order of methods
    |PETModel_V2.determine_potentialsoilevapotranspiration| and
    |PETModel_V2.determine_potentialwaterevaporation|.  All submodels following the
    |PETModel_V2| interface must work for both orders.
    """

    typeid: ClassVar[Literal[2]] = 2
    """Type identifier for |PETModel_V2| submodels."""

    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place."""

    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km²."""

    def prepare_zonetypes(self, zonetypes: Sequence[int]) -> None:
        """Set the types (usually land cover types) of the individual zones."""

    def prepare_water(self, water: VectorInputBool) -> None:
        """Set the flags for whether the individual zones are water areas or not."""

    def prepare_interception(self, interception: VectorInputBool) -> None:
        """Set the flags for whether interception evaporation is relevant for the
        individual zones."""

    def prepare_soil(self, soil: VectorInputBool) -> None:
        """Set the flags for whether soil evapotranspiration is relevant for the
        individual zones."""

    def prepare_plant(self, tree: VectorInputBool) -> None:
        """Set the flags for whether the individual zones contain any vegetation."""

    @modeltools.abstractmodelmethod
    def determine_potentialinterceptionevaporation(self) -> None:
        """Calculate potential interception evaporation."""

    @modeltools.abstractmodelmethod
    def get_potentialinterceptionevaporation(self, k: int) -> float:
        """Get the previously calculated potential interception evaporation of the
        selected zone in mm/T."""

    @modeltools.abstractmodelmethod
    def determine_potentialsoilevapotranspiration(self) -> None:
        """Calculate potential evapotranspiration from the soil."""

    @modeltools.abstractmodelmethod
    def get_potentialsoilevapotranspiration(self, k: int) -> float:
        """Get the previously calculated potential evapotranspiration from the soil of
        the selected zone in mm/T."""

    @modeltools.abstractmodelmethod
    def determine_potentialwaterevaporation(self) -> None:
        """Calculate potential evaporation from open water areas."""

    @modeltools.abstractmodelmethod
    def get_potentialwaterevaporation(self, k: int) -> float:
        """Get the previously calculated potential evaporation from open water areas of
        the selected zone in mm/T."""
