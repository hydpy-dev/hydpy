# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
# ...from hland
from hydpy.models.whmod import *
from hydpy.models.whmod import whmod_masks


class NutzNrComplete(parametertools.ZipParameter):
    MODEL_CONSTANTS = {
        key: value for key, value in whmod_constants.CONSTANTS.items()
        if value in (GRAS, LAUBWALD, MAIS, NADELWALD, SOMMERWEIZEN,
                     WINTERWEIZEN, ZUCKERRUEBEN, VERSIEGELT, WASSER)}
    mask = whmod_masks.NutzNrMask()

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area


class BodenTypComplete(parametertools.ZipParameter):
    MODEL_CONSTANTS = {
        key: value for key, value in whmod_constants.CONSTANTS.items()
        if value in (SAND, SAND_BINDIG, LEHM, TON, SCHLUFF, TORF)}
    mask = whmod_masks.BodenTypMask()

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area
