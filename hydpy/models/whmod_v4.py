# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""
External (FAO) reference evaporation without any interception evaporation.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import masktools
from hydpy.core import modeltools

# ...from arma
from hydpy.models.whmod import whmod_model
from hydpy.models.whmod import whmod_masks
from hydpy.models.whmod.whmod_constants import *


class Model(modeltools.AdHocModel):
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        whmod_model.Calc_NiederschlagRichter_V1,
        whmod_model.Calc_MaxVerdunstung_V2,
        whmod_model.Calc_Interzeptionsspeicher_V2,
        whmod_model.Calc_Seeniederschlag_V1,
        whmod_model.Calc_Oberflaechenabfluss_V1,
        whmod_model.Calc_ZuflussBoden_V1,
        whmod_model.Calc_RelBodenfeuchte_V1,
        whmod_model.Calc_Sickerwasser_V1,
        whmod_model.Calc_Bodenverdunstung_V1,
        whmod_model.Corr_Bodenverdunstung_V1,
        whmod_model.Calc_Seeverdunstung_V1,
        whmod_model.Calc_AktVerdunstung_V1,
        whmod_model.Calc_PotKapilAufstieg_V1,
        whmod_model.Calc_KapilAufstieg_V1,
        whmod_model.Calc_AktBodenwassergehalt_V1,
        whmod_model.Calc_PotGrundwasserneubildung_V1,
        whmod_model.Calc_AktGrundwasserneubildung_V1,
        whmod_model.Calc_VerzGrundwasserneubildung_Zwischenspeicher_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
