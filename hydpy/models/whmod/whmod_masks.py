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
    """Mask including all types of landuse classes."""
    RELEVANT_VALUES = (
        GRAS, LAUBWALD, MAIS, NADELWALD, SOMMERWEIZEN,
        WINTERWEIZEN, ZUCKERRUEBEN, VERSIEGELT, WASSER)

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |Nutz_Nr|."""
        return variable.subvars.vars.model.parameters.control.nutz_nr


class BodenTypMask(masktools.IndexMask):
    """Mask including all types of landuse classes."""
    RELEVANT_VALUES = (SAND, SAND_BINDIG, LEHM, TON, SCHLUFF, TORF)

    @staticmethod
    def get_refindices(variable):
        """Reference to the associated instance of |Nutz_Nr|."""
        return variable.subvars.vars.model.parameters.control.bodentyp


class Masks(masktools.Masks):
    #BASE2CONSTANTS = {NutzNrMask: whmod_constants.CONSTANTS}
    CLASSES = (NutzNrMask,
               BodenTypMask)
