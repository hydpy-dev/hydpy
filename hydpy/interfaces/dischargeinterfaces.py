"""This module defines interfaces for calculating discharge based on flow formulas or
rating curves."""

# import...
# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class DischargeModel_V1(modeltools.SubmodelInterface):
    """Simple interface for calculating discharge in m³/s based on the current water
    depth."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |DischargeModel_V1| submodels."""

    def prepare_channeldepth(self, channeldepth: float) -> None:
        """Set the channel depth in m."""

    def prepare_tolerance(self, tolerance: float) -> None:
        """Set the water depth-related smoothing parameter in m."""

    @modeltools.abstractmodelmethod
    def calculate_discharge(self, waterdepth: float) -> float:
        """Calculate the discharge based on the water depth given in m and return it in
        m³/s."""


class DischargeModel_V2(modeltools.SubmodelInterface):
    """Simple interface for calculating discharge in mm/T based on the current water
    depth."""

    typeid: ClassVar[Literal[2]] = 2
    """Type identifier for |DischargeModel_V2| submodels."""

    def prepare_channeldepth(self, channeldepth: float) -> None:
        """Set the channel depth in m."""

    def prepare_tolerance(self, tolerance: float) -> None:
        """Set the water depth-related smoothing parameter in m."""

    @modeltools.abstractmodelmethod
    def calculate_discharge(self, waterdepth: float) -> float:
        """Calculate the discharge based on the water depth given in m and return it in
        mm/T."""
