# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from standard library
import itertools

# ...from site-packages
import numpy

# ...from HydPy
from hydpy import pub
from hydpy.core import parametertools
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_masks
from hydpy.models.whmod import whmod_parameters


class Area(parametertools.Parameter):
    """[m²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NmbZones(parametertools.Parameter):
    """[-]"""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        model = self.subpars.pars.model
        for subvars in itertools.chain(model.parameters, model.sequences):
            for var in subvars:
                if var.NDIM == 1:
                    var.shape = self.value


class ZoneArea(whmod_parameters.NutzCompleteParameter):
    """[m²]"""

    SPAN = (0.0, None)

class LandType(parametertools.NameParameter):
    """[-]"""

    constants = whmod_constants.LANDUSE_CONSTANTS


class SoilType(parametertools.NameParameter):
    """[-]"""

    constants = whmod_constants.SOIL_CONSTANTS



class DegreeFactor(whmod_parameters.NutzBodenParameter):
    """[mm/T/K]"""

    SPAN = (0.0, None)


class CapillaryRise(parametertools.Parameter):
    """[-]"""

    NDIM, TYPE, TIME = 0, bool, None



class MaxInterz(whmod_parameters.LanduseMonthParameter):  # ToDo
    """[mm]"""


class FLN(whmod_parameters.LanduseMonthParameter):  # ToDo
    """[-]"""



whmod_parameters.BodenCompleteParameter.CONTROLPARAMETERS = (NmbZones, SoilType)  # ToDo


class NFK100_Mittel(whmod_parameters.NutzBodenParameter):
    """[mm/m]"""

    SPAN = (0.0, None)


class Flurab(whmod_parameters.NutzBodenParameter):
    """[m]"""

    SPAN = (0.0, None)


class MaxWurzeltiefe(whmod_parameters.NutzBodenParameter):
    """Maximale Wurzeltiefe [m]

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(1)
    >>> landtype(1)
    >>> maxwurzeltiefe(gras=5.)
    >>> maxwurzeltiefe
    maxwurzeltiefe(5.0)
    """

    SPAN = (0.0, None)


class MinhasR(whmod_parameters.NutzBodenParameter):
    """[-]"""

    SPAN = (0.1, None)


class KapilSchwellwert(whmod_parameters.BodenCompleteParameter):
    """[-]"""

    SPAN = (0.0, None)


class KapilGrenzwert(whmod_parameters.BodenCompleteParameter):
    """[-]"""

    SPAN = (0.0, None)


class BFI(whmod_parameters.NutzLandParameter):
    """Base Flow Index [-]."""

    SPAN = (0.0, None)


class Schwerpunktlaufzeit(parametertools.Parameter):
    """Schwerpunktlaufzeit [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)

    def __call__(self, *args, **kwargs):
        """
        Vergleiche Abbildung 7 in WHM_TipsTricks_5:

        >>> from hydpy import pub, print_vector
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.whmod import *
        >>> parameterstep("1d")
        >>> for h in range(-1, 11):
        ...     schwerpunktlaufzeit(flurab_probst=h)
        ...     print_vector([h, schwerpunktlaufzeit.value])
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

        >>> parameterstep("1h")
        >>> schwerpunktlaufzeit
        schwerpunktlaufzeit(58079.95344)

        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1h"
        >>> schwerpunktlaufzeit(flurab_probst=10.0)
        >>> schwerpunktlaufzeit
        schwerpunktlaufzeit(58079.95344)
        >>> parameterstep("1d")
        >>> schwerpunktlaufzeit
        schwerpunktlaufzeit(2419.99806)
        """
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            if (len(kwargs) == 1) and ("flurab_probst" in kwargs):
                x = kwargs["flurab_probst"]
                k_d = 0.6 * (((5.8039 * x - 21.899) * x + 41.933) * x + 0.0001)
                k_t = 60 * 60 * 24 * k_d / pub.timegrids.init.stepsize.seconds
                self.value = max(k_t, 0.0)
            else:
                raise NotImplementedError('"flurab_probst" oder Zahl.')
