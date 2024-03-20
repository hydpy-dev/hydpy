# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
from __future__ import annotations

# ...from HydPy
from hydpy.core import masktools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.models.evap import evap_control


class Soil(masktools.SubmodelIndexMask):
    """Mask including hydrological response units where evapotranspiration from soils
    occurs."""

    @staticmethod
    def get_refinement(variable: variabletools.Variable) -> evap_control.Soil:
        """Return a reference to the associated |evap_control.Soil| instance."""
        return variable.subvars.vars.model.parameters.control.soil


class Plant(masktools.SubmodelIndexMask):
    """Mask including hydrological response units containing any vegetation."""

    @staticmethod
    def get_refinement(variable: variabletools.Variable) -> evap_control.Plant:
        """Return a reference to the associated |evap_control.Plant| instance."""
        return variable.subvars.vars.model.parameters.control.plant


class Water(masktools.SubmodelIndexMask):
    """Mask including hydrological response units where evaporation from open water
    areas."""

    @staticmethod
    def get_refinement(variable: variabletools.Variable) -> evap_control.Water:
        """Return a reference to the associated |evap_control.Water| instance."""
        return variable.subvars.vars.model.parameters.control.water


class Masks(masktools.Masks):
    """Masks of base model |evap|."""

    CLASSES = (Soil, Plant, Water)
