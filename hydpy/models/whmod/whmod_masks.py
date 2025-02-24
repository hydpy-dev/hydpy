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
        LAUBWALD,
        MAIS,
        NADELWALD,
        SOMMERWEIZEN,
        WINTERWEIZEN,
        ZUCKERRUEBEN,
        VERSIEGELT,
        WASSER,
    )


class NutzLand(NutzBase):
    """Land Nutzungsklassen"""

    relevant: tuple[parametertools.IntConstant, ...] = (
        GRAS,
        LAUBWALD,
        MAIS,
        NADELWALD,
        SOMMERWEIZEN,
        WINTERWEIZEN,
        ZUCKERRUEBEN,
        VERSIEGELT,
    )


class NutzBoden(NutzBase):
    """Boden Nutzungsklassen"""

    relevant: tuple[parametertools.IntConstant, ...] = (
        GRAS,
        LAUBWALD,
        MAIS,
        NADELWALD,
        SOMMERWEIZEN,
        WINTERWEIZEN,
        ZUCKERRUEBEN,
    )


class NutzGras(NutzBase):
    """Gras Nutzungsklasse"""

    relevant = (GRAS,)


class NutzLaubwald(NutzBase):
    """Laubwald Nutzungsklasse"""

    relevant = (LAUBWALD,)


class NutzMais(NutzBase):
    """Mais Nutzungsklasse"""

    relevant = (MAIS,)


class NutzNadelwald(NutzBase):
    """Nadelwald Nutzungsklasse"""

    relevant = (NADELWALD,)


class NutzSommerweizen(NutzBase):
    """Sommerweizen Nutzungsklasse"""

    relevant = (SOMMERWEIZEN,)


class NutzWinterweizen(NutzBase):
    """Winterweizen Nutzungsklasse"""

    relevant = (WINTERWEIZEN,)


class NutzZuckerrueben(NutzBase):
    """Zuckerrüben Nutzungsklasse"""

    relevant = (ZUCKERRUEBEN,)


class NutzVersiegelt(NutzBase):
    """Versiegelt Nutzungsklasse"""

    relevant = (VERSIEGELT,)


class NutzWasser(NutzBase):
    """Wasser Nutzungsklasse"""

    relevant = (WASSER,)


class BodenComplete(masktools.IndexMask):
    """Bodenklassen"""

    relevant = (SAND, SAND_BINDIG, LEHM, TON, SCHLUFF, TORF)

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
