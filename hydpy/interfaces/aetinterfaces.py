"""This module defines submodel interfaces for calculating actual evapotranspiration."""

# import...
# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class AETModel_V1(modeltools.SubmodelInterface):
    """Interface for calculating interception evaporation, evapotranspiration from
    soils, evaporation from water areas in separate steps.

    An essential note for model developers: All main models using the |AETModel_V1|
    interface must first call |AETModel_V1.determine_interceptionevaporation| but are
    free to choose the execution order of methods
    |AETModel_V1.determine_soilevapotranspiration| and
    |AETModel_V1.determine_waterevaporation|.  All submodels following the
    |AETModel_V1| interface must work for both orders.  Additionally, the main model
    must calculate its snow routine (if it has one) before calling any method defined
    by the |AETModel_V1| interface.
    """

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |AETModel_V1| submodels."""

    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones in which the actual calculations take place."""

    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the areas of the individual zones in km²."""

    def prepare_elevations(self, elevations: Sequence[float]) -> None:
        """Set the elevations of the individual zones in m."""

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

    def prepare_tree(self, tree: VectorInputBool) -> None:
        """Set the flags for whether the individual zones contain tree-like
        vegetation."""

    def prepare_conifer(self, conifer: VectorInputBool) -> None:
        """Set the flags for whether the individual zones contain conifer-like
        vegetation."""

    def prepare_measuringheightwindspeed(self, measuringheightwindspeed: float) -> None:
        """Set the height above the ground of the wind speed measurements in m."""

    def prepare_leafareaindex(self, maxsoilwater: MatrixInputFloat) -> None:
        """Set the leaf area index in m²/m²."""

    def prepare_maxsoilwater(self, maxsoilwater: VectorInputFloat) -> None:
        """Set the maximum soil water content in mm."""

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
