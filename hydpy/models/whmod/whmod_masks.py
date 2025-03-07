# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.core import parametertools

# ...from hland
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod.whmod_constants import *


def _exclude(*args):
    return tuple(
        value
        for (key, value) in whmod_constants.LANDTYPE_CONSTANTS.items()
        if value not in args
    )


class LandTypeBase(masktools.IndexMask):
    """Nutzungsbasisklasse"""

    @staticmethod
    def get_refindices(variable):
        return variable.subvars.vars.model.parameters.control.landtype


class LandTypeComplete(LandTypeBase):
    """Alle Nutzungsklassen"""

    relevant: _exclude()


class LandTypeNonWater(LandTypeBase):
    """Land Nutzungsklassen"""

    relevant: _exclude(WATER)


class LandTypeGroundwater(LandTypeBase):
    """Land Nutzungsklassen"""

    relevant: _exclude(SEALED)


class LandTypeSoil(LandTypeBase):
    """Boden Nutzungsklassen"""

    relevant: _exclude(SEALED, WATER)


class LandTypeGras(LandTypeBase):
    """Gras Nutzungsklasse"""

    relevant = (GRAS,)


class LandTypeDecidious(LandTypeBase):
    """Laubwald Nutzungsklasse"""

    relevant = (DECIDIOUS,)


class LandTypeCorn(LandTypeBase):
    """Mais Nutzungsklasse"""

    relevant = (CORN,)


class LandTypeConifer(LandTypeBase):
    """Nadelwald Nutzungsklasse"""

    relevant = (CONIFER,)


class LandTypeSpringWheat(LandTypeBase):
    """Sommerweizen Nutzungsklasse"""

    relevant = (SPRINGWHEAT,)


class LandTypeWinterWheat(LandTypeBase):
    """Winterweizen Nutzungsklasse"""

    relevant = (WINTERWHEAT,)


class LandTypeSugarbeets(LandTypeBase):
    """Zuckerrüben Nutzungsklasse"""

    relevant = (SUGARBEETS,)


class LandTypeSealed(LandTypeBase):
    """Versiegelt Nutzungsklasse"""

    relevant = (SEALED,)


class LandTypeWater(LandTypeBase):
    """Wasser Nutzungsklasse"""

    relevant = (WATER,)


class SoilTypeBase(masktools.IndexMask):
    """Bodenklassen"""

    @staticmethod
    def get_refindices(variable):
        return variable.subvars.vars.model.parameters.control.soiltype


class SoilTypeComplete(SoilTypeBase):
    """Bodenklassen"""

    relevant = (SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT)


class SoilTypeSand(SoilTypeBase):
    """Bodenklassen"""

    relevant = (SAND,)


class SoilTypeSandCohesive(SoilTypeBase):
    """Bodenklassen"""

    relevant = (SAND_COHESIVE,)


class SoilTypeLoam(SoilTypeBase):
    """Bodenklassen"""

    relevant = (LOAM,)


class SoilTypeClay(SoilTypeBase):
    """Bodenklassen"""

    relevant = (CLAY,)


class SoilTypeSilt(SoilTypeBase):
    """Bodenklassen"""

    relevant = (SILT,)


class SoilTypePeat(SoilTypeBase):
    """Bodenklassen"""

    relevant = (PEAT,)


class Masks(masktools.Masks):
    CLASSES = (
        LandTypeComplete,
        LandTypeNonWater,
        LandTypeSoil,
        LandTypeGras,
        LandTypeDecidious,
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
