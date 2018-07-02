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
from hydpy.models.lland.lland_constants import (
    SIED_D, SIED_L, VERS, ACKER, WEINB, OBSTB, BODEN, GLETS, GRUE_I, FEUCHT,
    GRUE_E, BAUMB, NADELW, LAUBW, MISCHW, WASSER, FLUSS, SEE)


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


class Sied_D(Complete):
    """Mask for land use |SIED_D|."""
    RELEVANT_VALUES = (SIED_D,)


class Sied_L(Complete):
    """Mask for land use |SIED_L|."""
    RELEVANT_VALUES = (SIED_L,)


class Vers(Complete):
    """Mask for land use |VERS|."""
    RELEVANT_VALUES = (VERS,)


class Acker(Complete):
    """Mask for land use |ACKER|."""
    RELEVANT_VALUES = (ACKER,)


class Weinb(Complete):
    """Mask for land use |WEINB|."""
    RELEVANT_VALUES = (WEINB,)


class Obstb(Complete):
    """Mask for land use |OBSTB|."""
    RELEVANT_VALUES = (OBSTB,)


class Boden(Complete):
    """Mask for land use |BODEN|."""
    RELEVANT_VALUES = (BODEN,)


class Glets(Complete):
    """Mask for land use |GLETS|."""
    RELEVANT_VALUES = (GLETS,)


class Grue_I(Complete):
    """Mask for land use |GRUE_I|."""
    RELEVANT_VALUES = (GRUE_I,)


class Feucht(Complete):
    """Mask for land use |FEUCHT|."""
    RELEVANT_VALUES = (FEUCHT,)


class Grue_E(Complete):
    """Mask for land use |GRUE_E|."""
    RELEVANT_VALUES = (GRUE_E,)


class Baumb(Complete):
    """Mask for land use |BAUMB|."""
    RELEVANT_VALUES = (BAUMB,)


class Nadelw(Complete):
    """Mask for land use |NADELW|."""
    RELEVANT_VALUES = (NADELW,)


class Laubw(Complete):
    """Mask for land use |LAUBW|."""
    RELEVANT_VALUES = (LAUBW,)


class Mischw(Complete):
    """Mask for land use |MISCHW|."""
    RELEVANT_VALUES = (MISCHW,)


class Wasser(Complete):
    """Mask for land use |WASSER|."""
    RELEVANT_VALUES = (WASSER,)


class Fluss(Complete):
    """Mask for land use |FLUSS|."""
    RELEVANT_VALUES = (FLUSS,)


class See(Complete):
    """Mask for land use |SEE|."""
    RELEVANT_VALUES = (SEE,)


class Masks(masktools.Masks):
    """Masks of base model |lland|."""
    CLASSES = (Complete,
               Land,
               Soil,
               Sied_D,
               Sied_L,
               Vers,
               Acker,
               Weinb,
               Obstb,
               Boden,
               Glets,
               Grue_I,
               Feucht,
               Grue_E,
               Baumb,
               Nadelw,
               Laubw,
               Mischw,
               Wasser,
               Fluss,
               See)
