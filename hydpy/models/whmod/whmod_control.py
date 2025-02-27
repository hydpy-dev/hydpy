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


class InterceptionCapacity(whmod_parameters.LanduseMonthParameter):
    """[mm]"""


class DegreeDayFactor(whmod_parameters.NutzBodenParameter):
    """[mm/T/K]"""

    SPAN = (0.0, None)


class AvailableFieldCapacity(whmod_parameters.NutzBodenParameter):
    """[mm/m]"""

    SPAN = (0.0, None)


class RootingDepth(whmod_parameters.NutzBodenParameter):
    """Maximale Wurzeltiefe [m]

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(1)
    >>> landtype(1)
    >>> rootingdepth(gras=5.0)
    >>> rootingdepth
    rootingdepth(5.0)
    """

    SPAN = (0.0, None)


class GroundwaterDepth(whmod_parameters.NutzBodenParameter):
    """[m]"""

    SPAN = (0.0, None)


class CapillaryRise(parametertools.Parameter):
    """[-]"""

    NDIM, TYPE, TIME = 0, bool, None


class CapillaryThreshold(whmod_parameters.BodenCompleteParameter):
    """[-]"""

    SPAN = (0.0, None)


class CapillaryLimit(whmod_parameters.BodenCompleteParameter):
    """[-]"""

    SPAN = (0.0, None)


class BaseflowIndex(whmod_parameters.NutzLandParameter):
    """Baseflow index [-]."""

    SPAN = (0.0, None)


class RechargeDelay(parametertools.Parameter):
    """Schwerpunktlaufzeit [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)



whmod_parameters.BodenCompleteParameter.CONTROLPARAMETERS = (NmbZones, SoilType)  # ToDo
