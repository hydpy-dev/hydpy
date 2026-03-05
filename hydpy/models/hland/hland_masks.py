# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.core import variabletools
from hydpy.core.typingtools import *

# ...from hland
# from hydpy.models.hland import hland_model  # actual import below
from hydpy.models.hland.hland_constants import FIELD, FOREST, ILAKE, GLACIER, SEALED

if TYPE_CHECKING:
    from hydpy.models.hland import hland_control


class HLandBaseMask(masktools.IndexMask):
    """To be overridden."""

    @staticmethod
    def get_refindices(variable: variabletools.Variable) -> hland_control.ZoneType:
        """Reference to the associated instance of |ZoneType|."""
        # pylint: disable=import-outside-toplevel
        from hydpy.models.hland import hland_model

        model = cast(hland_model.Model, variable.subvars.vars.model)
        return model.parameters.control.zonetype


class Complete(HLandBaseMask):
    """Mask including all types of zones."""

    relevant = (FIELD, FOREST, ILAKE, GLACIER, SEALED)


class Land(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, |GLACIER|, and |SEALED|."""

    relevant = (FIELD, FOREST, GLACIER, SEALED)


class Interception(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |SEALED|."""

    relevant = (FIELD, FOREST, SEALED)


class Snow(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, |GLACIER|, and |SEALED|."""

    relevant = (FIELD, FOREST, GLACIER, SEALED)


class Soil(HLandBaseMask):
    """Mask including zones of type |FIELD| and |FOREST|."""

    relevant = (FIELD, FOREST)


class UpperZone(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |GLACIER|."""

    relevant = (FIELD, FOREST, GLACIER)


class Field(HLandBaseMask):
    """Mask for zone type |FIELD|."""

    relevant = (FIELD,)


class Forest(HLandBaseMask):
    """Mask for zone type |FOREST|."""

    relevant = (FOREST,)


class ILake(HLandBaseMask):
    """Mask for zone type |ILAKE|."""

    relevant = (ILAKE,)


class Glacier(HLandBaseMask):
    """Mask for zone type |GLACIER|."""

    relevant = (GLACIER,)


class Sealed(HLandBaseMask):
    """Mask for zone type |SEALED|."""

    relevant = (SEALED,)


class NoGlacier(HLandBaseMask):
    """Mask including zones of type |FIELD|, |FOREST|, and |ILAKE|."""

    relevant = (FIELD, FOREST, ILAKE, SEALED)


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
