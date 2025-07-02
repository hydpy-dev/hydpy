# pylint: disable=missing-module-docstring

from hydpy.core import masktools

from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod.whmod_constants import *


def _exclude(*args):
    return tuple(
        value
        for (key, value) in whmod_constants.LANDTYPE_CONSTANTS.items()
        if value not in args
    )


class LandTypeBase(masktools.IndexMask):
    """Base class for all land type-specific masks."""

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |LandType|."""
        return variable.subvars.vars.model.parameters.control.landtype


class LandTypeComplete(LandTypeBase):
    """Mask that includes all land use types."""

    relevant = _exclude()


class LandTypeNonWater(LandTypeBase):
    """Mask that excludes water areas."""

    relevant = _exclude(WATER)


class LandTypeGroundwater(LandTypeBase):
    """Mask that includes all areas with groundwater recharge."""

    relevant = _exclude(SEALED)


class LandTypeSoil(LandTypeBase):
    """Mask that includes areas with soils."""

    relevant = _exclude(SEALED, WATER)


class LandTypeGras(LandTypeBase):
    """Mask that includes only grassland."""

    relevant = (GRASS,)


class LandTypeDeciduous(LandTypeBase):
    """Mask that includes only decidious forests."""

    relevant = (DECIDUOUS,)


class LandTypeCorn(LandTypeBase):
    """Mask that includes only corn fields."""

    relevant = (CORN,)


class LandTypeConifer(LandTypeBase):
    """Mask that includes only conifer forests."""

    relevant = (CONIFER,)


class LandTypeSpringWheat(LandTypeBase):
    """Mask that includes only spring wheat fields."""

    relevant = (SPRINGWHEAT,)


class LandTypeWinterWheat(LandTypeBase):
    """Mask that includes only winter wheat fields."""

    relevant = (WINTERWHEAT,)


class LandTypeSugarbeets(LandTypeBase):
    """Mask that includes only sugar beet fields."""

    relevant = (SUGARBEETS,)


class LandTypeSealed(LandTypeBase):
    """Mask that includes only sealed areas."""

    relevant = (SEALED,)


class LandTypeWater(LandTypeBase):
    """Mask that includes only water areas."""

    relevant = (WATER,)


class SoilTypeBase(masktools.IndexMask):
    """Base class for all soil type-specific masks."""

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |SoilType|."""
        return variable.subvars.vars.model.parameters.control.soiltype


class SoilTypeComplete(SoilTypeBase):
    """Mask that includes all soil types."""

    relevant = (SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT)


class SoilTypeSand(SoilTypeBase):
    """Mask that includes only sand soils."""

    relevant = (SAND,)


class SoilTypeSandCohesive(SoilTypeBase):
    """Mask that includes only cohesive sand soils."""

    relevant = (SAND_COHESIVE,)


class SoilTypeLoam(SoilTypeBase):
    """Mask that includes only loam soils."""

    relevant = (LOAM,)


class SoilTypeClay(SoilTypeBase):
    """Mask that includes only clay soils."""

    relevant = (CLAY,)


class SoilTypeSilt(SoilTypeBase):
    """Mask that includes only silt soils."""

    relevant = (SILT,)


class SoilTypePeat(SoilTypeBase):
    """Mask that includes only peat soils."""

    relevant = (PEAT,)


class Masks(masktools.Masks):
    """Masks of |whmod.DOCNAME.complete|."""

    CLASSES = (
        LandTypeComplete,
        LandTypeNonWater,
        LandTypeSoil,
        LandTypeGras,
        LandTypeDeciduous,
        LandTypeCorn,
        LandTypeConifer,
        LandTypeSpringWheat,
        LandTypeWinterWheat,
        LandTypeSugarbeets,
        LandTypeSealed,
        LandTypeWater,
        SoilTypeComplete,
        SoilTypeSand,
        SoilTypeSandCohesive,
        SoilTypeLoam,
        SoilTypeClay,
        SoilTypeSilt,
        SoilTypePeat,
    )
