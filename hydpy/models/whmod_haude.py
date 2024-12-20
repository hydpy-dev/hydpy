# pylint: disable=unused-wildcard-import
"""Haude-Dommermuth-Trumpf version of WHMod.

Unterschiede zum Original-WHMod:

  * vollständigere Ausgaben
  * Korrektur Bodenwasserbilanz
  * Korrektur Beta-Berechnung
  * BFI-Berücksichtigung?
  * Linearspeicher bilanztreuer?
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.models.whmod import whmod_model
from hydpy.models.whmod.whmod_constants import *


class Model(modeltools.AdHocModel):
    """Haude-Dommermuth-Trumpf version of WHMod."""

    DOCNAME = modeltools.DocName(short="WHMod-Haude", description="Haude-Dommermuth-Trumpf evapotranspiration")

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        whmod_model.Calc_NiederschlagRichter_V1,
        whmod_model.Calc_Saettigungsdampfdruckdefizit_V1,
        whmod_model.Calc_MaxVerdunstung_V1,
        whmod_model.Calc_NiedNachInterz_V1,
        whmod_model.Calc_InterzeptionsVerdunstung_V1,
        whmod_model.Calc_Seeniederschlag_V1,
        whmod_model.Calc_Oberflaechenabfluss_V1,
        whmod_model.Calc_ZuflussBoden_V1,
        whmod_model.Calc_RelBodenfeuchte_V1,
        whmod_model.Calc_Sickerwasser_V1,
        whmod_model.Calc_Bodenverdunstung_V1,
        whmod_model.Calc_Seeverdunstung_V1,
        whmod_model.Calc_AktVerdunstung_V1,
        whmod_model.Calc_PotKapilAufstieg_V1,
        whmod_model.Calc_KapilAufstieg_V1,
        whmod_model.Calc_AktBodenwassergehalt_V1,
        whmod_model.Calc_PotGrundwasserneubildung_V1,
        whmod_model.Calc_Basisabfluss_V1,
        whmod_model.Calc_AktGrundwasserneubildung_V1,
        whmod_model.Calc_VerzGrundwasserneubildung_Zwischenspeicher_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
