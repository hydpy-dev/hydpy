# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import masktools
from hydpy.core import parametertools

# ...from hland
from hydpy.models.whmod.whmod_constants import *


class NutzBase(masktools.IndexMask):
    """Nutzungsbasisklasse"""

    @staticmethod
    def get_refindices(variable):
        return variable.subvars.vars.model.parameters.control.landtype


class NutzComplete(NutzBase):
    """Alle Nutzungsklassen"""

    relevant: tuple[parametertools.IntConstant, ...] = (
        GRAS,
        DECIDIOUS,
        CORN,
        CONIFER,
        SPRINGWHEAT,
        WINTERWHEAT,
        SUGARBEETS,
        SEALED,
        WATER,
    )


class NutzLand(NutzBase):
    """Land Nutzungsklassen"""

    relevant: tuple[parametertools.IntConstant, ...] = (
        GRAS,
        DECIDIOUS,
        CORN,
        CONIFER,
        SPRINGWHEAT,
        WINTERWHEAT,
        SUGARBEETS,
        SEALED,
    )


class NutzBoden(NutzBase):
    """Boden Nutzungsklassen"""

    relevant: tuple[parametertools.IntConstant, ...] = (
        GRAS,
        DECIDIOUS,
        CORN,
        CONIFER,
        SPRINGWHEAT,
        WINTERWHEAT,
        SUGARBEETS,
    )


class NutzGras(NutzBase):
    """Gras Nutzungsklasse"""

    relevant = (GRAS,)


class NutzLaubwald(NutzBase):
    """Laubwald Nutzungsklasse"""

    relevant = (DECIDIOUS,)


class NutzMais(NutzBase):
    """Mais Nutzungsklasse"""

    relevant = (CORN,)


class NutzNadelwald(NutzBase):
    """Nadelwald Nutzungsklasse"""

    relevant = (CONIFER,)


class NutzSommerweizen(NutzBase):
    """Sommerweizen Nutzungsklasse"""

    relevant = (SPRINGWHEAT,)


class NutzWinterweizen(NutzBase):
    """Winterweizen Nutzungsklasse"""

    relevant = (WINTERWHEAT,)


class NutzZuckerrueben(NutzBase):
    """Zuckerrüben Nutzungsklasse"""

    relevant = (SUGARBEETS,)


class NutzVersiegelt(NutzBase):
    """Versiegelt Nutzungsklasse"""

    relevant = (SEALED,)


class NutzWasser(NutzBase):
    """Wasser Nutzungsklasse"""

    relevant = (WATER,)


class BodenComplete(masktools.IndexMask):
    """Bodenklassen"""

    relevant = (SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT)

    @staticmethod
    def get_refindices(variable):
        return variable.subvars.vars.model.parameters.control.soiltype


class Masks(masktools.Masks):
    CLASSES = (
        NutzComplete,
        NutzLand,
        NutzBoden,
        NutzGras,
        NutzLaubwald,
        NutzMais,
        NutzNadelwald,
        NutzSommerweizen,
        NutzWinterweizen,
        NutzZuckerrueben,
        NutzVersiegelt,
        NutzWasser,
        BodenComplete,
    )
