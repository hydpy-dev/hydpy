# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
import itertools
# from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import parametertools
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_masks


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


TEMP = {key: value for key, value in whmod_constants.CONSTANTS.items()
        if value in (GRAS, LAUBWALD, MAIS, NADELWALD, SOMMERWEIZEN,
                     WINTERWEIZEN, ZUCKERRUEBEN, VERSIEGELT, WASSER)}


class Nutz_Nr(parametertools.NameParameter):
    """[-]"""
    NDIM, TYPE, TIME = 1, int, None
    CONSTANTS = TEMP
    SPAN = min(CONSTANTS.values()), max(CONSTANTS.values())


class NutzNrComplete(parametertools.ZipParameter):

    CONTROLPARAMETERS = (
        Nutz_Nr,
        Nmb_Cells,
    )

    MODEL_CONSTANTS = TEMP
    mask = whmod_masks.NutzNrMask()

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area


del TEMP

TEMP = {key: value for key, value in whmod_constants.CONSTANTS.items()
        if value in (SAND, SAND_BINDIG, LEHM, TON, SCHLUFF, TORF)}


class BodenTyp(parametertools.NameParameter):
    """[-]"""
    NDIM, TYPE, TIME = 1, int, None
    CONSTANTS = TEMP
    SPAN = min(CONSTANTS.values()), max(CONSTANTS.values())


class BodenTypComplete(parametertools.ZipParameter):

    CONTROLPARAMETERS = (
        BodenTyp,
        Nmb_Cells,
    )

    MODEL_CONSTANTS = TEMP
    mask = whmod_masks.BodenTypMask()

    @property
    def shapeparameter(self):
        return self.subpars.pars.control.nmb_cells

    @property
    def refweights(self):
        return self.subpars.pars.control.f_area


del TEMP


class F_AREA(NutzNrComplete):
    """[m²]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class LanduseMonthParameter(parametertools.KeywordParameter2D):
    TYPE, TIME, SPAN = float, None, (0., None)
    COLNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    ROWNAMES = ('gras', 'laubwald', 'mais', 'nadelwald', 'sommerweizen',
                'winterweizen', 'zuckerrueben', 'versiegelt', 'wasser')


class MaxInterz(LanduseMonthParameter):
    """[mm]"""


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


class FLN(LanduseMonthParameter):
    """[-]"""


class Gradfaktor(NutzNrComplete):
    """[mm/T/K]"""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)


class NFK100_Mittel(NutzNrComplete):
    """[mm/m]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class Flurab(NutzNrComplete):
    """[m]"""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class MaxWurzeltiefe(NutzNrComplete):
    """[m]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class MinhasR(NutzNrComplete):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (.1, None)


class KapilSchwellwert(BodenTypComplete):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class KapilGrenzwert(BodenTypComplete):
    """[-]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class BFI(BodenTypComplete):
    """Base Flow Index [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class Schwerpunktlaufzeit(parametertools.Parameter):
    """Schwerpunktlaufzeit [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)

    def __call__(self, *args, **kwargs):
        """
        Vergleiche Abbildung 7 in WHM_TipsTricks_5:

        >>> from hydpy import pub, print_values
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'
        >>> from hydpy.models.whmod import *
        >>> parameterstep('1d')
        >>> for h in range(-1, 11):
        ...     schwerpunktlaufzeit(flurab_probst=h)
        ...     print_values([h, schwerpunktlaufzeit.value])
        -1, 0.0
        0, 0.00006
        1, 15.5028
        2, 25.62078
        3, 51.24804
        4, 113.27862
        5, 232.60656
        6, 430.1259
        7, 726.73068
        8, 1143.31494
        9, 1700.77272
        10, 2419.99806

        >>> schwerpunktlaufzeit
        schwerpunktlaufzeit(2419.99806)

        >>> parameterstep('1h')
        >>> schwerpunktlaufzeit
        schwerpunktlaufzeit(58079.95344)

        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1h'
        >>> schwerpunktlaufzeit(flurab_probst=10.0)
        >>> schwerpunktlaufzeit
        schwerpunktlaufzeit(58079.95344)
        >>> parameterstep('1d')
        >>> schwerpunktlaufzeit
        schwerpunktlaufzeit(2419.99806)
        """
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            if (len(kwargs) == 1) and ('flurab_probst' in kwargs):
                x = kwargs['flurab_probst']
                k_d = .6*(((5.8039*x-21.899)*x+41.933)*x+.0001)
                self.value = max(
                    60*60*24*k_d/pub.timegrids.init.stepsize.seconds, 0.)
            else:
                raise NotImplementedError(
                    '"flurab_probst" oder Zahl.')
