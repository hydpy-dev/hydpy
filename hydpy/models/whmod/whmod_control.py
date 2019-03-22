# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
import itertools
# from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools
# ...from hland
from hydpy.core import objecttools
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_parameters


class Area(parametertools.Parameter):
    """[m²]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class Nmb_Cells(parametertools.Parameter):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        model = self.subpars.pars.model
        for subvars in itertools.chain(model.parameters, model.sequences):
            for var in subvars:
                if var.NDIM == 1:
                    var.shape = self.value


class KorrNiedNachRichter(parametertools.Parameter):
    """[-]"""
    NDIM, TYPE, TIME = 0, bool, None

    def __call__(self, *args, **kwargs):
        if args[0]:
            raise NotImplementedError(
                'Richterkorrektur fehlt noch')
        super().__call__(*args, **kwargs)


class InterzeptionNach_Dommermuth_Trampf(parametertools.Parameter):
    """[-]"""
    NDIM, TYPE, TIME = 0, bool, None

    def __call__(self, *args, **kwargs):
        if not args[0]:
            raise NotImplementedError(
                'Bislang nur Dommermuth-Trampf möglich')
        super().__call__(*args, **kwargs)


class MitFunktion_KapillarerAufstieg(parametertools.Parameter):
    """[-]"""
    NDIM, TYPE, TIME = 1, bool, None


class Nutz_Nr(parametertools.NameParameter):
    """[-]"""
    NDIM, TYPE, TIME = 1, int, None
    CONSTANTS = whmod_parameters.NutzNrComplete.MODEL_CONSTANTS
    SPAN = min(CONSTANTS.values()), max(CONSTANTS.values())


class BodenTyp(parametertools.NameParameter):
    """[-]"""
    NDIM, TYPE, TIME = 1, int, None
    CONSTANTS = whmod_parameters.BodenTypComplete.MODEL_CONSTANTS
    SPAN = min(CONSTANTS.values()), max(CONSTANTS.values())


class F_AREA(whmod_parameters.NutzNrComplete):
    """[m²]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class Faktor(parametertools.KeywordParameter2D):
    TYPE, TIME, SPAN = float, None, (0., None)
    COLNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    ROWNAMES = ('gras', 'laubwald', 'mais', 'nadelwald', 'sommerweizen',
                'winterweizen', 'zuckerrueben', 'versiegelt', 'wasser')


class FactorC(parametertools.KeywordParameter2D):
    TYPE, TIME, SPAN = float, None, (0., None)
    COLNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    ROWNAMES = ('laubwald', 'nadelwald')


class FaktorWald(parametertools.KeywordParameter2D):
    TYPE, TIME, SPAN = float, None, (0., None)
    COLNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    ROWNAMES = ('laubwald', 'nadelwald')


class Gradfaktor(whmod_parameters.NutzNrComplete):
    """[mm/T/K]"""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)


class NFK100_Mittel(whmod_parameters.NutzNrComplete):
    """[mm/m]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class Flurab(whmod_parameters.NutzNrComplete):
    """[m]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class MaxWurzeltiefe(whmod_parameters.NutzNrComplete):
    """[m]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class MinhasR(whmod_parameters.NutzNrComplete):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (.1, None)


class KapilSchwellwert(whmod_parameters.BodenTypComplete):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class KapilGrenzwert(whmod_parameters.BodenTypComplete):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class ControlParameters(parametertools.SubParameters):
    CLASSES = (Area,
               Nmb_Cells,
               KorrNiedNachRichter,
               InterzeptionNach_Dommermuth_Trampf,
               MitFunktion_KapillarerAufstieg,
               Nutz_Nr,
               BodenTyp,
               Faktor,
               FactorC,
               FaktorWald,
               F_AREA,
               Gradfaktor,
               NFK100_Mittel,
               Flurab,
               MaxWurzeltiefe,
               MinhasR,
               KapilSchwellwert,
               KapilGrenzwert)

