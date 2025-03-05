# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy import pub
from hydpy.core import parametertools

# ...from whmod
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_parameters
from hydpy.models.whmod import whmod_control


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class ZoneRatio(whmod_parameters.NutzCompleteParameter):
    """[-]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (whmod_control.Area, whmod_control.ZoneArea)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> landtype(GRAS, WATER, SEALED)
        >>> area(100.0)
        >>> zonearea(20.0, 30.0, 50.0)
        >>> derived.zoneratio.update()
        >>> derived.zoneratio
        zoneratio(gras=0.2, sealed=0.5, water=0.3)
        """
        control = self.subpars.pars.control
        self(control.zonearea / control.area)


class SoilDepth(whmod_parameters.NutzBodenParameter):
    """[m]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.RootingDepth, whmod_control.GroundwaterDepth)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(5)
        >>> landtype(GRAS, DECIDIOUS, CONIFER, WATER, SEALED)
        >>> groundwaterdepth(1.0)
        >>> rootingdepth(0.5, 1.0, 1.5, 2.0, 2.0)
        >>> derived.soildepth.update()
        >>> derived.soildepth
        soildepth(conifer=1.0, decidious=1.0, gras=0.5)
        """
        control = self.subpars.pars.control
        self(numpy.clip(control.rootingdepth, None, control.groundwaterdepth.values))


class MaxSoilWater(whmod_parameters.NutzBodenParameter):
    """[mm]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.AvailableFieldCapacity,)
    DERIVEDPARAMETERS = (SoilDepth,)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(7)
        >>> landtype(GRAS, CORN, DECIDIOUS, CONIFER, SPRINGWHEAT, WATER, SEALED)
        >>> availablefieldcapacity(0.2)
        >>> derived.soildepth(0.0, 0.2, 0.3, 0.4, 1.0, 1.0, 1.0)
        >>> derived.maxsoilwater.update()
        >>> derived.maxsoilwater
        maxsoilwater(conifer=80.0, corn=60.0, decidious=60.0, gras=60.0,
                     springwheat=200.0)
        """
        availablefieldcapacity = self.subpars.pars.control.availablefieldcapacity
        soildepth = self.subpars.soildepth
        self(1000.0 * availablefieldcapacity * numpy.clip(soildepth, 0.3, None))


class Beta(whmod_parameters.NutzBodenParameter):
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.LandType,)
    DERIVEDPARAMETERS = (MaxSoilWater,)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(26)
        >>> landtype(GRAS)
        >>> derived.maxsoilwater(range(0, 260, 10))
        >>> derived.beta.update()
        >>> from hydpy import print_vector
        >>> for values in zip(derived.maxsoilwater, derived.beta):
        ...     print_vector(values)
        0.0, 1.0
        10.0, 1.000001
        20.0, 1.000058
        30.0, 1.000806
        40.0, 1.005223
        50.0, 1.022215
        60.0, 1.072058
        70.0, 1.192281
        80.0, 1.438593
        90.0, 1.869943
        100.0, 2.510161
        110.0, 3.307578
        120.0, 4.143126
        130.0, 4.895532
        140.0, 5.498714
        150.0, 5.945944
        160.0, 6.262712
        170.0, 6.48211
        180.0, 6.632992
        190.0, 6.736978
        200.0, 6.809179
        210.0, 6.859826
        220.0, 6.895768
        230.0, 6.921582
        240.0, 6.940345
        250.0, 6.954142

        >>> nmbzones(2)
        >>> landtype(WATER, SEALED)
        >>> derived.maxsoilwater(100.0)
        >>> derived.beta.update()
        >>> derived.beta
        beta(nan)
        """
        landtype = self.subpars.pars.control.landtype
        maxsoilwater = self.subpars.maxsoilwater
        self(0.0)
        idxs1 = (landtype.values != WATER) * (landtype.values != SEALED)
        idxs2 = maxsoilwater.values <= 0.0
        idxs3 = idxs1 * idxs2
        self.values[idxs3] = 1.0
        idxs4 = idxs1 * ~idxs2
        self.values[idxs4] = 1.0 + 6.0 / (1 + (maxsoilwater[idxs4] / 118.25) ** -6.5)


class PotentialCapillaryRise(whmod_parameters.NutzBodenParameter):
    """Potential capillary rise [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)

    CONTROLPARAMETERS = (
        whmod_control.LandType,
        whmod_control.SoilType,
        whmod_control.CapillaryThreshold,
        whmod_control.CapillaryLimit,
        whmod_control.GroundwaterDepth,
    )
    DERIVEDPARAMETERS = (SoilDepth,)

    def update(self):
        """

        >>> from hydpy.models.whmod import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> landtype(GRAS, GRAS, GRAS, GRAS, GRAS, WATER, SEALED)
        >>> soiltype(SAND, SAND, SAND, SAND, SAND, INT_NAN, INT_NAN)
        >>> capillarythreshold(sand=0.8)
        >>> capillarylimit(sand=0.4)
        >>> derived.soildepth(sand=1.0)
        >>> groundwaterdepth(1.2, 1.4, 1.6, 1.8, 2.0, nan, nan)
        >>> derived.potentialcapillaryrise.update()
        >>> derived.potentialcapillaryrise
        """
        con = model.parameters.control
        idxs = (con.landtype == SEALED) * (con.landtype == WATER)
        flu.potentialcapillaryrise[idxs] = 0.0
        idxs = ~idxs
        flu.potentialcapillaryrise[idxs] = 5.0 * numpy.clip(
            (
                model.parameters.derived.soildepth[idxs]
                + con.capillarythreshold[idxs]
                - con.groundwaterdepth[idxs]
            )
            / (con.capillarythreshold[idxs] - con.capillarylimit[idxs]),
            0.0,
            1.0,
        )
