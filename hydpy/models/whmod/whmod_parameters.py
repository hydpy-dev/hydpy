# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_masks

# ToDo: NutzNrLand, NutzNrSoil, NutzNrSealed, NutzNrWater
# ToDo: the same for sequences


class NutzNrComplete(parametertools.ZipParameter):

    MODEL_CONSTANTS = whmod_constants.LANDUSE_CONSTANTS
    mask = whmod_masks.NutzNrMask()

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area


class BodenTypComplete(parametertools.ZipParameter):

    MODEL_CONSTANTS = whmod_constants.SOIL_CONSTANTS
    mask = whmod_masks.BodenTypMask()

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area


class LanduseMonthParameter(parametertools.KeywordParameter2D):
    TYPE, TIME, SPAN = float, None, (0.0, None)
    COLNAMES = (
        "jan",
        "feb",
        "mar",
        "apr",
        "mai",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    )
    ROWNAMES = (
        "gras",
        "laubwald",
        "mais",
        "nadelwald",
        "sommerweizen",
        "winterweizen",
        "zuckerrueben",
        "versiegelt",
        "wasser",
    )
