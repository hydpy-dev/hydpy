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
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from arma
from hydpy.models.whmod import whmod_model
from hydpy.models.whmod import whmod_control
from hydpy.models.whmod import whmod_derived
from hydpy.models.whmod import whmod_fluxes
from hydpy.models.whmod import whmod_inputs
from hydpy.models.whmod import whmod_states
from hydpy.models.whmod import whmod_masks
from hydpy.models.whmod.whmod_constants import *


class Model(modeltools.Model):
    RUN_METHODS = (
        whmod_model.calc_niederschlagrichter_v1,
        whmod_model.calc_maxverdunstung_v2,
        whmod_model.calc_interzeptionsspeicher_v1,
        whmod_model.calc_seeniederschlag_v1,
        whmod_model.calc_oberflaechenabfluss_v1,
        whmod_model.calc_zuflussboden_v1,
        whmod_model.calc_relbodenfeuchte_v1,
        whmod_model.calc_sickerwasser_v1,
        whmod_model.calc_bodenverdunstung_v1,
        whmod_model.corr_bodenverdunstung_v1,
        whmod_model.calc_seeverdunstung_v1,
        whmod_model.calc_aktverdunstung_v1,
        whmod_model.calc_potkapilaufstieg_v1,
        whmod_model.calc_kapilaufstieg_v1,
        whmod_model.calc_aktbodenwassergehalt_v1,
        whmod_model.calc_aktgrundwasserneubildung_v1)
    OUTLET_METHODS = ()


class ControlParameters(parametertools.SubParameters):
    CLASSES = (
        whmod_control.Area,
        whmod_control.Nmb_Cells,
        whmod_control.KorrNiedNachRichter,
        whmod_control.MitFunktion_KapillarerAufstieg,
        whmod_control.Nutz_Nr,
        whmod_control.BodenTyp,
        whmod_control.MaxInterz,
        whmod_control.FLN,
        whmod_control.F_AREA,
        whmod_control.Gradfaktor,
        whmod_control.NFK100_Mittel,
        whmod_control.Flurab,
        whmod_control.MaxWurzeltiefe,
        whmod_control.MinhasR,
        whmod_control.KapilSchwellwert,
        whmod_control.KapilGrenzwert)


class DerivedParameters(parametertools.SubParameters):
    CLASSES = (
        whmod_derived.MOY,
        whmod_derived.RelArea,
        whmod_derived.Wurzeltiefe,
        whmod_derived.nFKwe,
        whmod_derived.Beta)


class InputSequences(sequencetools.InputSequences):
    CLASSES = (
        whmod_inputs.Niederschlag,
        whmod_inputs.Temp_TM,
        whmod_inputs.ET0)


class FluxSequences(sequencetools.FluxSequences):
    CLASSES = (
        whmod_fluxes.NiederschlagRichter,
        whmod_fluxes.InterzeptionsVerdunstung,
        whmod_fluxes.NiedNachInterz,
        whmod_fluxes.Seeniederschlag,
        whmod_fluxes.ZuflussBoden,
        whmod_fluxes.Oberflaechenabfluss,
        whmod_fluxes.RelBodenfeuchte,
        whmod_fluxes.Sickerwasser,
        whmod_fluxes.MaxVerdunstung,
        whmod_fluxes.Bodenverdunstung,
        whmod_fluxes.Seeverdunstung,
        whmod_fluxes.AktVerdunstung,
        whmod_fluxes.PotKapilAufstieg,
        whmod_fluxes.KapilAufstieg,
        whmod_fluxes.AktGrundwasserneubildung)


class StateSequences(sequencetools.StateSequences):
    CLASSES = (
        whmod_states.Interzeptionsspeicher,
        whmod_states.Schneespeicher,
        whmod_states.AktBodenwassergehalt)


class Masks(masktools.Masks):
    CLASSES = (
        whmod_masks.NutzNrMask,
        whmod_masks.NutzLand,
        whmod_masks.NutzBoden,
        whmod_masks.NutzGras,
        whmod_masks.NutzLaubwald,
        whmod_masks.NutzMais,
        whmod_masks.NutzNadelwald,
        whmod_masks.NutzSommerweizen,
        whmod_masks.NutzWinterweizen,
        whmod_masks.NutzZuckerrueben,
        whmod_masks.NutzVersiegelt,
        whmod_masks.NutzWasser,
        whmod_masks.BodenTypMask)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
