# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import masktools
# ...model specific
from hydpy.models.hland import hland_constants
from hydpy.models.hland.hland_constants import FIELD, FOREST, ILAKE, GLACIER


class Complete(masktools.IndexMask):
    """Mask including all types of zones."""
    RELEVANT_VALUES = (FIELD, FOREST, ILAKE, GLACIER)

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |ZoneType|."""
        return variable.subvars.vars.model.parameters.control.zonetype


class Land(Complete):
    """Mask including zones of type |FIELD|, |FOREST|, and |GLACIER|."""
    RELEVANT_VALUES = (FIELD, FOREST, GLACIER)


class NoGlacier(Complete):
    """Mask including zones of type |FIELD|, |FOREST|, and |ILAKE|."""
    RELEVANT_VALUES = (FIELD, FOREST, ILAKE)


class Soil(Complete):
    """Mask including zones of type |FIELD| and |FOREST|."""
    RELEVANT_VALUES = (FIELD, FOREST)


class Masks(masktools.Masks):
    """Masks of base model |hland|."""
    BASE2CONSTANTS = {Complete: hland_constants.CONSTANTS}
    CLASSES = (Complete,
               Land,
               NoGlacier,
               Soil)
