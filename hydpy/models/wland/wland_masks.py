# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.models.wland import wland_constants


class Complete(masktools.IndexMask):
    """Mask including all land use types."""

    RELEVANT_VALUES = tuple(wland_constants.LANDUSE_CONSTANTS.values())

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |LT|."""
        return variable.subvars.vars.model.parameters.control.lt


class Masks(masktools.Masks):
    """Masks of base model |wland|."""

    CLASSES = (Complete,)
