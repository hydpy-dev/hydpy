# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from standard library
import itertools

# ...from site-packages
import numpy

# ...from HydPy
from hydpy import pub
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_masks
from hydpy.models.whmod import whmod_parameters


class Area(parametertools.Parameter):
    """Total area [m²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NmbZones(parametertools.Parameter):
    """Number of zones (hydrological response units) in a subbasin [-].

    |NmbZones| determines the length of most 1-dimensional parameters and sequences.
    Usually, you should first prepare |NmbZones| and define the values of all
    1-dimensional parameters and sequences afterwards:

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> availablefieldcapacity.shape
    (5,)
    >>> states.soilmoisture.shape
    (5,)

    Changing the value of |NmbZones| later reshapes the affected parameters and
    sequences and makes it necessary to reset their values:

    >>> availablefieldcapacity(2.0)
    >>> availablefieldcapacity
    availablefieldcapacity(2.0)
    >>> nmbzones(3)
    >>> availablefieldcapacity
    availablefieldcapacity(?)

    Re-defining the same value does not delete the already available data:

    >>> availablefieldcapacity(2.0)
    >>> nmbzones(3)
    >>> availablefieldcapacity
    availablefieldcapacity(2.0)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new = self.value
        if new != old:
            model = self.subpars.pars.model
            for subvars in itertools.chain(model.parameters, model.sequences):
                for var in subvars:
                    if var.NDIM == 1:
                        var.shape = new


class ZoneArea(whmod_parameters.NutzCompleteParameter):
    """Zone area [m²]."""

    SPAN = (0.0, None)


class LandType(parametertools.NameParameter):
    """Land cover type [-]."""

    constants = whmod_constants.LANDUSE_CONSTANTS


class SoilType(parametertools.NameParameter):
    """Soil type [-]."""

    constants = whmod_constants.SOIL_CONSTANTS
    mask = whmod_masks.NutzBoden()


class InterceptionCapacity(whmod_parameters.LanduseMonthParameter):
    """Maximum interception storage [mm]."""


class DegreeDayFactor(whmod_parameters.NutzBodenParameter):
    """Degree day factor for snow melting [mm/T/K]."""

    TIME , SPAN= True, (0.0, None)


class AvailableFieldCapacity(whmod_parameters.NutzBodenParameter):
    """Maximum relative soil moisture content [-]."""

    TIME, SPAN = True, (0.0, None)


class RootingDepth(whmod_parameters.NutzBodenParameter):
    """Maximum rooting depth [m]."""

    TIME, SPAN = None, (0.0, None)


class GroundwaterDepth(whmod_parameters.NutzBodenParameter):
    """Average groundwater depth [m]."""

    TIME, SPAN = None, (0.0, None)


class WithCapillaryRise(parametertools.Parameter):
    """Flag to enable/disable capillary rise [-]."""

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
