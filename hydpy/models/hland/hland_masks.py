# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
# ...from hland
from hydpy.models.hland import hland_constants
from hydpy.models.hland.hland_constants import FIELD, FOREST, ILAKE, GLACIER


class BaseMask(masktools.IndexMask):
    """To be overridden."""

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |ZoneType|."""
        return variable.subvars.vars.model.parameters.control.zonetype


class Complete(BaseMask):
    """Mask including all types of zones."""
    RELEVANT_VALUES = (FIELD, FOREST, ILAKE, GLACIER)


class Land(BaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |GLACIER|."""
    RELEVANT_VALUES = (FIELD, FOREST, GLACIER)


class NoGlacier(BaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |ILAKE|."""
    RELEVANT_VALUES = (FIELD, FOREST, ILAKE)


class Soil(BaseMask):
    """Mask including zones of type |FIELD| and |FOREST|."""
    RELEVANT_VALUES = (FIELD, FOREST)


class Field(BaseMask):
    """Mask for zone type |FIELD|."""
    RELEVANT_VALUES = (FIELD,)


class Forest(BaseMask):
    """Mask for zone type |FOREST|."""
    RELEVANT_VALUES = (FOREST,)


class ILake(BaseMask):
    """Mask for zone type |ILAKE|."""
    RELEVANT_VALUES = (ILAKE,)


class Glacier(BaseMask):
    """Mask for zone type |GLACIER|."""
    RELEVANT_VALUES = (GLACIER,)


class Masks(masktools.Masks):
    """Masks of base model |hland|."""
    CLASSES = (Complete,
               Land,
               NoGlacier,
               Soil,
               Field,
               Forest,
               ILake,
               Glacier)
