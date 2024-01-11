"""This module defines submodel interfaces for providing radiation-related data."""
# import...
# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class RadiationModel_V1(modeltools.SharableSubmodelInterface):
    """Simple interface for determining all data in one step."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |RadiationModel_V1| submodels."""

    @modeltools.abstractmodelmethod
    def process_radiation(self) -> None:
        """Read and calculate all eventually required sunshine and radiation data."""

    @modeltools.abstractmodelmethod
    def get_possiblesunshineduration(self) -> float:
        """Get the possible sunshine duration in h."""

    @modeltools.abstractmodelmethod
    def get_sunshineduration(self) -> float:
        """Get the sunshine duration in h."""

    @modeltools.abstractmodelmethod
    def get_clearskysolarradiation(self) -> float:
        """Get the clear sky solar radiation in W/m²."""

    @modeltools.abstractmodelmethod
    def get_globalradiation(self) -> float:
        """Get the global radiation in W/m²."""


class RadiationModel_V2(modeltools.SharableSubmodelInterface):
    """Pure getter interface for global radiation."""

    typeid: ClassVar[Literal[2]] = 2
    """Type identifier for |RadiationModel_V2| submodels."""

    @modeltools.abstractmodelmethod
    def get_globalradiation(self) -> float:
        """Get the global radiation in W/m²."""


class RadiationModel_V3(modeltools.SharableSubmodelInterface):
    """Pure getter interface for clear-sky solar radiation and global radiation."""

    typeid: ClassVar[Literal[3]] = 3
    """Type identifier for |RadiationModel_V3| submodels."""

    @modeltools.abstractmodelmethod
    def get_clearskysolarradiation(self) -> float:
        """Get the clear sky solar radiation in W/m²."""

    @modeltools.abstractmodelmethod
    def get_globalradiation(self) -> float:
        """Get the global radiation in W/m²."""


class RadiationModel_V4(modeltools.SharableSubmodelInterface):
    """Pure getter interface for possible sunshine duration, actual sunshine duration,
    and global radiation."""

    typeid: ClassVar[Literal[4]] = 4
    """Type identifier for |RadiationModel_V4| submodels."""

    @modeltools.abstractmodelmethod
    def get_possiblesunshineduration(self) -> float:
        """Get the possible sunshine duration in h."""

    @modeltools.abstractmodelmethod
    def get_sunshineduration(self) -> float:
        """Get the sunshine duration in h."""

    @modeltools.abstractmodelmethod
    def get_globalradiation(self) -> float:
        """Get the global radiation in W/m²."""
