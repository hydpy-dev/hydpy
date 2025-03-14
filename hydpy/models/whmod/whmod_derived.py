# pylint: disable=missing-module-docstring

import numpy

import hydpy
from hydpy.core import parametertools

from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod import whmod_parameters
from hydpy.models.whmod import whmod_control


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class ZoneRatio(whmod_parameters.LandTypeCompleteParameter):
    """Relative zone area [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (whmod_control.Area, whmod_control.ZoneArea)

    def update(self):
        """Calculate the relative zone areas based on
        :math:`ZoneRation = ZoneArea / Area`.

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> landtype(GRASS, WATER, SEALED)
        >>> area(100.0)
        >>> zonearea(20.0, 30.0, 50.0)
        >>> derived.zoneratio.update()
        >>> derived.zoneratio
        zoneratio(grass=0.2, sealed=0.5, water=0.3)
        """
        control = self.subpars.pars.control
        self.values = control.zonearea / control.area


class SoilDepth(whmod_parameters.SoilTypeParameter):
    """Effective soil depth [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.RootingDepth, whmod_control.GroundwaterDepth)

    def update(self):
        """Calculate the effective soil depth

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(4)
        >>> landtype(GRASS, DECIDUOUS, CONIFER, WATER)
        >>> soiltype(SAND, SILT, CLAY, NONE)
        >>> groundwaterdepth(1.0)
        >>> rootingdepth(0.5, 1.0, 1.5, 2.0)
        >>> derived.soildepth.update()
        >>> derived.soildepth
        soildepth(clay=1.0, sand=0.5, silt=1.0)
        """
        control = self.subpars.pars.control
        self.values = numpy.minimum(
            control.rootingdepth.values, control.groundwaterdepth.values
        )


class MaxSoilWater(whmod_parameters.SoilTypeParameter):
    """Maximum water content of the considered soil column [mm]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    CONTROLPARAMETERS = (
        whmod_control.AvailableFieldCapacity,
        whmod_control.RootingDepth,
    )
    DERIVEDPARAMETERS = (SoilDepth,)

    def update(self):
        r"""Calculate the maximum soil water content based on
        :math:`1000 \cdot AvailableFieldCapacity \cdot max(SoilDepth, \, 0.3)`

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(7)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, NONE)
        >>> availablefieldcapacity(0.2)
        >>> derived.soildepth(
        ...     sand=0.0, sand_cohesive=0.2, loam=0.3, clay=0.4, silt=1.0, peat=1.0
        ... )
        >>> derived.maxsoilwater.update()
        >>> derived.maxsoilwater
        maxsoilwater(clay=80.0, loam=60.0, peat=200.0, sand=60.0,
                     sand_cohesive=60.0, silt=200.0)
        """
        availablefieldcapacity = self.subpars.pars.control.availablefieldcapacity
        soildepth = self.subpars.soildepth
        self(1000.0 * availablefieldcapacity * numpy.maximum(soildepth, 0.3))


class Beta(whmod_parameters.SoilTypeParameter):
    """Nonlinearity parameter for calculating percolation [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    CONTROLPARAMETERS = (whmod_control.SoilType,)
    DERIVEDPARAMETERS = (MaxSoilWater,)

    def update(self):
        r"""Calculate |Beta| based on
        :math:`1 + \frac{6}{1 + (MaxSoilWater / 118.25)^{-6.5}}`
        :cite:p:`ref-Armbruster2002`.

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> nmbzones(7)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, NONE)
        >>> derived.maxsoilwater(
        ...     sand=0.0, sand_cohesive=50.0, loam=100.0, clay=150.0, silt=200.0,
        ...     peat=250.0
        ... )
        >>> derived.beta.update()
        >>> derived.beta
        beta(clay=5.945944, loam=2.510161, peat=6.954142, sand=1.0,
             sand_cohesive=1.022215, silt=6.809179)

        >>> nmbzones(2)
        >>> landtype(WATER, SEALED)
        >>> soiltype(NONE)
        >>> derived.maxsoilwater(100.0)
        >>> derived.beta.update()
        >>> derived.beta
        beta(nan)
        """
        maxsoilwater = self.subpars.maxsoilwater
        self.values = numpy.nan
        idxs1 = self.subpars.pars.control.soiltype.values != NONE
        idxs2 = maxsoilwater.values <= 0.0
        idxs3 = idxs1 * idxs2
        self.values[idxs3] = 1.0
        idxs4 = idxs1 * ~idxs2
        self.values[idxs4] = 1.0 + 6.0 / (1 + (maxsoilwater[idxs4] / 118.25) ** -6.5)


class PotentialCapillaryRise(whmod_parameters.SoilTypeParameter):
    """Potential capillary rise [mm/T]."""

    TYPE, TIME, SPAN = float, True, (0.0, None)

    CONTROLPARAMETERS = (
        whmod_control.SoilType,
        whmod_control.CapillaryThreshold,
        whmod_control.CapillaryLimit,
        whmod_control.RootingDepth,
        whmod_control.GroundwaterDepth,
    )
    DERIVEDPARAMETERS = (SoilDepth,)

    def update(self):
        r"""Calculate the potential capillary rise based on
        :math:`5 \cdot Days \cdot
        \frac{(GroundwaterDepth - SoilDepth) - CapillaryThreshold}
        {CapillaryLimit - CapillaryThreshold}`.

        >>> from hydpy.models.whmod import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nmbzones(7)
        >>> landtype(GRASS, GRASS, GRASS, GRASS, GRASS, GRASS, SEALED)
        >>> soiltype(SAND, SAND, SAND, SAND, SAND, SAND, NONE)
        >>> capillarythreshold(sand=0.8)
        >>> capillarylimit(sand=0.4)
        >>> derived.soildepth(sand=1.0)
        >>> groundwaterdepth(1.2, 1.4, 1.6, 1.8, 2.0, nan, nan)
        >>> derived.potentialcapillaryrise.update()
        >>> derived.potentialcapillaryrise
        potentialcapillaryrise(5.0, 5.0, 2.5, 0.0, 0.0, nan, nan)
        >>> from hydpy import print_vector
        >>> print_vector(derived.potentialcapillaryrise.values)
        0.208333, 0.208333, 0.104167, 0.0, 0.0, nan, nan

        >>> capillarythreshold(sand=0.6)
        >>> capillarylimit(sand=0.6)
        >>> derived.potentialcapillaryrise.update()
        >>> derived.potentialcapillaryrise
        potentialcapillaryrise(5.0, 5.0, 0.0, 0.0, 0.0, nan, nan)
        """

        self.values = numpy.nan
        values = self.values
        maxrise = 5.0 * hydpy.pub.options.simulationstep.days
        control = self.subpars.pars.control
        for i, (soiltype, threshold, limit, delta) in enumerate(
            zip(
                control.soiltype.values,
                control.capillarythreshold.values,
                control.capillarylimit.values,
                control.groundwaterdepth.values - self.subpars.soildepth.values,
            )
        ):
            if soiltype != NONE:
                if delta >= threshold:
                    values[i] = 0.0
                elif delta <= limit:
                    values[i] = maxrise
                else:
                    values[i] = maxrise * ((delta - threshold) / (limit - threshold))
