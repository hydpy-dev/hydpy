# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import masktools
# ...model specific
from hydpy.models.lland import lland_constants
from hydpy.models.lland.lland_constants import WASSER, SEE, FLUSS, VERS


def _exclude(*args):
    return tuple(
        value for (key, value) in lland_constants.CONSTANTS.items()
        if value not in args)


class Complete(masktools.IndexMask):
    """Mask including all land uses."""
    RELEVANT_VALUES = _exclude()

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |Lnk|."""
        return variable.subvars.vars.model.parameters.control.lnk


class Land(Complete):
    """Mask excluding the land uses |WASSER|, |SEE| and |FLUSS|."""
    RELEVANT_VALUES = _exclude(WASSER, SEE, FLUSS)


class Soil(Complete):
    """Mask excluding the land uses |WASSER|, |SEE|, |FLUSS|, and |VERS|."""
    RELEVANT_VALUES = _exclude(WASSER, SEE, FLUSS, VERS)


class Masks(masktools.Masks):
    """Masks of base model |lland|."""
    BASE2CONSTANTS = {Complete: lland_constants.CONSTANTS}
    CLASSES = (Complete,
               Land,
               Soil)
