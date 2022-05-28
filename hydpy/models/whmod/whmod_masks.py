# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import masktools

# ...from hland
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod.whmod_constants import *


class NutzComplete(masktools.IndexMask):
    RELEVANT_VALUES = (
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

    @staticmethod
    def get_refindices(variable):
        return variable.subvars.vars.model.parameters.control.nutz_nr


class NutzLand(NutzComplete):
    RELEVANT_VALUES = (
        GRAS,
        LAUBWALD,
        MAIS,
        NADELWALD,
        SOMMERWEIZEN,
        WINTERWEIZEN,
        ZUCKERRUEBEN,
        VERSIEGELT,
    )


class NutzBoden(NutzComplete):
    RELEVANT_VALUES = (
        GRAS,
        LAUBWALD,
        MAIS,
        NADELWALD,
        SOMMERWEIZEN,
        WINTERWEIZEN,
        ZUCKERRUEBEN,
    )


class NutzGras(NutzComplete):
    RELEVANT_VALUES = (GRAS,)


class NutzLaubwald(NutzComplete):
    RELEVANT_VALUES = (LAUBWALD,)


class NutzMais(NutzComplete):
    RELEVANT_VALUES = (MAIS,)


class NutzNadelwald(NutzComplete):
    RELEVANT_VALUES = (NADELWALD,)


class NutzSommerweizen(NutzComplete):
    RELEVANT_VALUES = (SOMMERWEIZEN,)


class NutzWinterweizen(NutzComplete):
    RELEVANT_VALUES = (WINTERWEIZEN,)


class NutzZuckerrueben(NutzComplete):
    RELEVANT_VALUES = (ZUCKERRUEBEN,)


class NutzVersiegelt(NutzComplete):
    RELEVANT_VALUES = (VERSIEGELT,)


class NutzWasser(NutzComplete):
    RELEVANT_VALUES = (WASSER,)


class BodenComplete(masktools.IndexMask):
    RELEVANT_VALUES = (SAND, SAND_BINDIG, LEHM, TON, SCHLUFF, TORF)

    @staticmethod
    def get_refindices(variable):
        return variable.subvars.vars.model.parameters.control.bodentyp


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
