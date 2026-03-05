# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

from hydpy.models.wland import wland_model
from hydpy.models.wland import wland_constants
from hydpy.models.wland import wland_control
from hydpy.models.wland.wland_constants import WATER, SEALED


def _exclude(*args: parametertools.IntConstant) -> tuple[int, ...]:
    return tuple(
        value for (key, value) in wland_constants.CONSTANTS.items() if value not in args
    )


class Complete(masktools.IndexMask):
    """Mask including all land use types."""

    relevant = _exclude()

    @staticmethod
    def get_refindices(variable: variabletools.Variable) -> wland_control.LT:
        """Reference to the associated instance of |LT|."""
        model = cast(wland_model.Model, variable.subvars.vars.model)
        return model.parameters.control.lt


class Land(Complete):
    """Mask excluding the land type |WATER|."""

    relevant = _exclude(WATER)


class Soil(Complete):
    """Mask excluding the land types |WATER| and |SEALED|."""

    relevant = _exclude(WATER, SEALED)


class Sealed(Complete):
    """Mask for the land type |SEALED|."""

    relevant = (SEALED,)


class Water(Complete):
    """Mask for the land type |WATER|."""

    relevant = (WATER,)


class Masks(masktools.Masks):
    """Masks of base model |wland|."""

    CLASSES = (Complete, Land, Soil, Sealed, Water)
