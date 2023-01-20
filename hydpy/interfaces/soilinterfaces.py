"""This module defines submodel interfaces for soil-related processes.

.. _`issue 89`: https://github.com/hydpy-dev/hydpy/issues/89

"""
# import...
# ...from standard library
from abc import abstractmethod
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

# ...from hydpy
from hydpy.core import modeltools


class SoilModel_V1(modeltools.SubmodelInterface):
    """Soil submodel interface for calculating infiltration and percolation in multiple
    soil compartments.

    |SoilModel_V1| is for submodels that update their states internally.   If the
    submodel calculates infiltration and percolation based on the given soil surface
    water supply, it also adjusts its soil moisture content.  Hence, it offers a method
    for getting the current soil water content (|SoilModel_V1.get_soilwatercontent|)
    but not for setting it.

    The reason for implementing |SoilModel_V1| was to couple |lland| with |ga_garto|,
    as discussed in `issue 89`_.

    All units in mm or mm/T.  The method parameter "k" is the index of the considered
    soil compartment.
    """

    typeid: ClassVar[Literal[1]] = 1

    @abstractmethod
    def set_initialsurfacewater(self, k: int, v: float) -> None:
        """Set the surface water depth initially ponded at the soil's surface.

        If the caller subtracts a fraction from the water reaching the surface before
        executing |SoilModel_V1.execute_infiltration|, he should pass the original
        (unreduced) water amount to |SoilModel_V1.set_initialsurfacewater|.
        """

    @abstractmethod
    def set_actualsurfacewater(self, k: int, v: float) -> None:
        """Set the surface water depth that is actually available for infiltration.

        If the caller subtracts a fraction from the water reaching the surface before
        executing |SoilModel_V1.execute_infiltration|, he should pass the resulting
        (reduced) water amount to |SoilModel_V1.set_actualsurfacewater|.
        """

    @abstractmethod
    def set_soilwatersupply(self, k: int, v: float) -> None:
        """Set the direct water supply to the soil's body (e.g. due to capillary
        rise)."""

    @abstractmethod
    def set_soilwaterdemand(self, k: int, v: float) -> None:
        """Set the direct water demand from the soil's body (e.g. due to
        evapotranspiration)."""

    @abstractmethod
    def execute_infiltration(self, k: int) -> None:
        """Execute the infiltration routine (that might also calculate percolation)
        based on the given surface water supply.
        """

    @abstractmethod
    def add_soilwater(self, k: int) -> None:
        """Add the given (direct) soil water supply."""

    @abstractmethod
    def remove_soilwater(self, k: int) -> None:
        """Remove the given (direct) soil water demand."""

    @abstractmethod
    def get_infiltration(self, k: int) -> float:
        """Get the previously calculated infiltration rate."""

    @abstractmethod
    def get_percolation(self, k: int) -> float:
        """Get the previously calculated percolation rate."""

    @abstractmethod
    def get_soilwateraddition(self, k: int) -> float:
        """Get the previously calculated actual soil water addition."""

    @abstractmethod
    def get_soilwaterremoval(self, k: int) -> float:
        """Get the previously calculated actual soil water removal."""

    @abstractmethod
    def get_soilwatercontent(self, k: int) -> float:
        """Get the current soil water content."""
