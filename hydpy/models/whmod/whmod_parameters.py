# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_masks


class NutzBaseParameter(parametertools.ZipParameter):
    NDIM, TYPE, TIME = 1, float, None

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area


class NutzCompleteParameter(NutzBaseParameter):

    MODEL_CONSTANTS = parametertools.Constants(
        **{
            key: value
            for key, value in whmod_constants.LANDUSE_CONSTANTS.items()
            if value in whmod_masks.NutzComplete.RELEVANT_VALUES
        }
    )
    mask = whmod_masks.NutzComplete()


class NutzLandParameter(NutzBaseParameter):

    MODEL_CONSTANTS = parametertools.Constants(
        **{
            key: value
            for key, value in whmod_constants.LANDUSE_CONSTANTS.items()
            if value in whmod_masks.NutzLand.RELEVANT_VALUES
        }
    )
    mask = whmod_masks.NutzLand()


class NutzBodenParameter(NutzBaseParameter):

    MODEL_CONSTANTS = parametertools.Constants(
        **{
            key: value
            for key, value in whmod_constants.LANDUSE_CONSTANTS.items()
            if value in whmod_masks.NutzBoden.RELEVANT_VALUES
        }
    )
    mask = whmod_masks.NutzBoden()


class BodenCompleteParameter(parametertools.ZipParameter):
    NDIM, TYPE, TIME = 1, float, None

    MODEL_CONSTANTS = whmod_constants.SOIL_CONSTANTS
    mask = whmod_masks.BodenComplete()

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area


class ForestMonthParameter(parametertools.KeywordParameter2D):
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
    ROWNAMES = ("laubwald", "nadelwald")


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
