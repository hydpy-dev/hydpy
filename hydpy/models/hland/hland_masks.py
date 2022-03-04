# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import masktools

# ...from hland
from hydpy.models.hland.hland_constants import FIELD, FOREST, ILAKE, GLACIER, SEALED


class HLandBaseMask(masktools.IndexMask):
    """To be overridden."""

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |ZoneType|."""
        return variable.subvars.vars.model.parameters.control.zonetype


class Complete(HLandBaseMask):
    """Mask including all types of zones."""

    RELEVANT_VALUES = (FIELD, FOREST, ILAKE, GLACIER, SEALED)


class Land(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, |GLACIER|, and |SEALED|."""

    RELEVANT_VALUES = (FIELD, FOREST, GLACIER, SEALED)


class Interception(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |SEALED|."""

    RELEVANT_VALUES = (FIELD, FOREST, SEALED)


class Snow(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, |GLACIER|, and |SEALED|."""

    RELEVANT_VALUES = (FIELD, FOREST, GLACIER, SEALED)


class Soil(HLandBaseMask):
    """Mask including zones of type |FIELD| and |FOREST|."""

    RELEVANT_VALUES = (FIELD, FOREST)


class UpperZone(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |GLACIER|."""

    RELEVANT_VALUES = (FIELD, FOREST, GLACIER)


class Field(HLandBaseMask):
    """Mask for zone type |FIELD|."""

    RELEVANT_VALUES = (FIELD,)


class Forest(HLandBaseMask):
    """Mask for zone type |FOREST|."""

    RELEVANT_VALUES = (FOREST,)


class ILake(HLandBaseMask):
    """Mask for zone type |ILAKE|."""

    RELEVANT_VALUES = (ILAKE,)


class Glacier(HLandBaseMask):
    """Mask for zone type |GLACIER|."""

    RELEVANT_VALUES = (GLACIER,)


class Sealed(HLandBaseMask):
    """Mask for zone type |SEALED|."""

    RELEVANT_VALUES = (SEALED,)


class NoGlacier(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |ILAKE|."""

    RELEVANT_VALUES = (FIELD, FOREST, ILAKE, SEALED)


class Masks(masktools.Masks):
    """Masks of base model |hland|."""

    CLASSES = (
        Complete,
        Land,
        UpperZone,
        Snow,
        Soil,
        Field,
        Forest,
        ILake,
        Glacier,
        Sealed,
        NoGlacier,
    )
