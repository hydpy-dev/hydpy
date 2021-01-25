# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import masktools

# ...from hland
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod.whmod_constants import *


class NutzNrMask(masktools.IndexMask):
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


class NutzLand(NutzNrMask):
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


class NutzBoden(NutzNrMask):
    RELEVANT_VALUES = (
        GRAS,
        LAUBWALD,
        MAIS,
        NADELWALD,
        SOMMERWEIZEN,
        WINTERWEIZEN,
        ZUCKERRUEBEN,
    )


class NutzGras(NutzNrMask):
    RELEVANT_VALUES = (GRAS,)


class NutzLaubwald(NutzNrMask):
    RELEVANT_VALUES = (LAUBWALD,)


class NutzMais(NutzNrMask):
    RELEVANT_VALUES = (MAIS,)


class NutzNadelwald(NutzNrMask):
    RELEVANT_VALUES = (NADELWALD,)


class NutzSommerweizen(NutzNrMask):
    RELEVANT_VALUES = (SOMMERWEIZEN,)


class NutzWinterweizen(NutzNrMask):
    RELEVANT_VALUES = (WINTERWEIZEN,)


class NutzZuckerrueben(NutzNrMask):
    RELEVANT_VALUES = (ZUCKERRUEBEN,)


class NutzVersiegelt(NutzNrMask):
    RELEVANT_VALUES = (VERSIEGELT,)


class NutzWasser(NutzNrMask):
    RELEVANT_VALUES = (WASSER,)


class BodenTypMask(masktools.IndexMask):
    RELEVANT_VALUES = (SAND, SAND_BINDIG, LEHM, TON, SCHLUFF, TORF)

    @staticmethod
    def get_refindices(variable):
        return variable.subvars.vars.model.parameters.control.bodentyp


class Masks(masktools.Masks):
    CLASSES = (
        NutzNrMask,
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
        BodenTypMask,
    )
