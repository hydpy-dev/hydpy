# pylint: disable=missing-module-docstring

# import...
# ...from standard library
from __future__ import annotations

# ...from HydPy
from hydpy.core import masktools
from hydpy.core import variabletools

# ...from lland
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_constants
from hydpy.models.lland.lland_constants import (
    SIED_D,
    SIED_L,
    VERS,
    ACKER,
    WEINB,
    OBSTB,
    BODEN,
    GLETS,
    GRUE_I,
    FEUCHT,
    GRUE_E,
    BAUMB,
    NADELW,
    LAUBW,
    MISCHW,
    WASSER,
    FLUSS,
    SEE,
)


def _exclude(*args):
    return tuple(
        value for (key, value) in lland_constants.CONSTANTS.items() if value not in args
    )


class Complete(masktools.IndexMask):
    """Mask including all land uses."""

    relevant = _exclude()

    @staticmethod
    def get_refindices(variable: variabletools.Variable) -> lland_control.Lnk:
        """Reference to the associated instance of |Lnk|."""
        return variable.subvars.vars.model.parameters.control.lnk


class Land(Complete):
    """Mask excluding the land uses |WASSER|, |SEE| and |FLUSS|."""

    relevant = _exclude(WASSER, SEE, FLUSS)


class Soil(Complete):
    """Mask excluding the land uses |WASSER|, |SEE|, |FLUSS|, and |VERS|."""

    relevant = _exclude(WASSER, SEE, FLUSS, VERS)


class Forest(Complete):
    """Mask including the land uses |LAUBW|, |MISCHW|, and |NADELW|."""

    relevant = (LAUBW, MISCHW, NADELW)


class Water(Complete):
    """Mask including the land uses |WASSER|, |SEE|, and |FLUSS|."""

    relevant = (WASSER, SEE, FLUSS)


class Sied_D(Complete):
    """Mask for land use |SIED_D|."""

    relevant = (SIED_D,)


class Sied_L(Complete):
    """Mask for land use |SIED_L|."""

    relevant = (SIED_L,)


class Vers(Complete):
    """Mask for land use |VERS|."""

    relevant = (VERS,)


class Acker(Complete):
    """Mask for land use |ACKER|."""

    relevant = (ACKER,)


class Weinb(Complete):
    """Mask for land use |WEINB|."""

    relevant = (WEINB,)


class Obstb(Complete):
    """Mask for land use |OBSTB|."""

    relevant = (OBSTB,)


class Boden(Complete):
    """Mask for land use |BODEN|."""

    relevant = (BODEN,)


class Glets(Complete):
    """Mask for land use |GLETS|."""

    relevant = (GLETS,)


class Grue_I(Complete):
    """Mask for land use |GRUE_I|."""

    relevant = (GRUE_I,)


class Feucht(Complete):
    """Mask for land use |FEUCHT|."""

    relevant = (FEUCHT,)


class Grue_E(Complete):
    """Mask for land use |GRUE_E|."""

    relevant = (GRUE_E,)


class Baumb(Complete):
    """Mask for land use |BAUMB|."""

    relevant = (BAUMB,)


class Nadelw(Complete):
    """Mask for land use |NADELW|."""

    relevant = (NADELW,)


class Laubw(Complete):
    """Mask for land use |LAUBW|."""

    relevant = (LAUBW,)


class Mischw(Complete):
    """Mask for land use |MISCHW|."""

    relevant = (MISCHW,)


class Wasser(Complete):
    """Mask for land use |WASSER|."""

    relevant = (WASSER,)


class Fluss(Complete):
    """Mask for land use |FLUSS|."""

    relevant = (FLUSS,)


class See(Complete):
    """Mask for land use |SEE|."""

    relevant = (SEE,)


class Masks(masktools.Masks):
    """Masks of base model |lland|."""

    CLASSES = (
        Complete,
        Land,
        Soil,
        Forest,
        Water,
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
        See,
    )
