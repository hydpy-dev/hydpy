# pylint: disable=missing-module-docstring

from __future__ import annotations

from hydpy.core import masktools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.models.snow import snow_control


class Land(masktools.SubmodelIndexMask):
    """ToDo"""

    @staticmethod
    def get_refinement(variable: variabletools.Variable) -> snow_control.Land:
        """Return a reference to the associated |snow_control.Land| instance."""
        return variable.subvars.vars.model.parameters.control.land


class Water(masktools.SubmodelIndexMask):
    """Mask including hydrological response units where evaporation from open water
    areas."""

    @staticmethod
    def get_refinement(variable: variabletools.Variable) -> snow_control.Water:
        """Return a reference to the associated |snow_control.Water| instance."""
        return variable.subvars.vars.model.parameters.control.water


class Masks(masktools.Masks):
    """Masks of base model |snow|."""

    CLASSES = (Land, Water)
