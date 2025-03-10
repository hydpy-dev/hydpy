# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
from __future__ import annotations

# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_control
from hydpy.models.whmod import whmod_masks


class LandTypeBaseParameter(parametertools.ZipParameter):
    """Base class for 1-dimensional land type-specific parameters."""
    TYPE = float

    constants = whmod_constants.LANDTYPE_CONSTANTS

    @property
    def refweights(self):
        """Reference to the associated instance of |ZoneRatio| for calculating areal
        mean values."""
        return self.subpars.pars.control.zonearea


class LandTypeCompleteParameter(LandTypeBaseParameter):
    """Base class for 1-dimensional land type-specific parameters without restrictions.

    We take parameter |ZoneArea| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(grass=1.0, decidious=2.0, corn=3.0, conifer=4.0, springwheat=5.0,
    ...          winterwheat=6.0, sugarbeets=7.0, sealed=8.0, water=9.0)
    >>> zonearea
    zonearea(conifer=4.0, corn=3.0, decidious=2.0, grass=1.0, sealed=8.0,
             springwheat=5.0, sugarbeets=7.0, water=9.0, winterwheat=6.0)
    >>> from hydpy import round_
    >>> round_(zonearea.average_values())
    6.333333
    """

    mask = whmod_masks.LandTypeComplete()


class LandTypeNonWaterParameter(LandTypeBaseParameter):
    """Base class for 1-dimensional land type-specific parameters that do not affect
    water areas.

    We take parameter |DegreeDayFactor| as an example:

    >>> from hydpy.models.whmod import *
    >>> simulationstep("1d")
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> degreedayfactor(grass=1.0, decidious=2.0, corn=3.0, conifer=4.0, springwheat=5.0,
    ...                 winterwheat=6.0, sugarbeets=7.0, sealed=8.0)
    >>> degreedayfactor
    degreedayfactor(conifer=4.0, corn=3.0, decidious=2.0, grass=1.0,
                    sealed=8.0, springwheat=5.0, sugarbeets=7.0,
                    winterwheat=6.0)
    >>> zonearea(0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.9)
    >>> from hydpy import round_
    >>> round_(degreedayfactor.average_values())
    3.333333
    """

    mask = whmod_masks.LandTypeNonWater()


class LandTypeGroundwaterParameter(LandTypeBaseParameter):
    """Base class for 1-dimensional land type-specific parameters that affect
    groundwater recharge.

    We take parameter |BaseflowIndex| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          WATER, SEALED)
    >>> baseflowindex(grass=0.1, decidious=0.2, corn=0.3, conifer=0.4, springwheat=0.5,
    ...               winterwheat=0.6, sugarbeets=0.7, water=0.8)
    >>> baseflowindex
    baseflowindex(conifer=0.4, corn=0.3, decidious=0.2, grass=0.1,
                  springwheat=0.5, sugarbeets=0.7, water=0.8,
                  winterwheat=0.6)
    >>> zonearea(8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 9.0)
    >>> from hydpy import round_
    >>> round_(baseflowindex.average_values())
    0.333333
    """

    mask = whmod_masks.LandTypeGroundwater()


class LandTypeSoilParameter(LandTypeBaseParameter):
    """Base class for 1-dimensional land type-specific parameters that affect soil
    processes.

    We take parameter |RootingDepth| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDIOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          WATER, SEALED)
    >>> rootingdepth(grass=0.1, decidious=0.2, corn=0.3, conifer=0.4, springwheat=0.5,
    ...              winterwheat=0.6, sugarbeets=0.7)
    >>> rootingdepth
    rootingdepth(conifer=0.4, corn=0.3, decidious=0.2, grass=0.1,
                 springwheat=0.5, sugarbeets=0.7, winterwheat=0.6)
    >>> zonearea(7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 8.0, 9.0)
    >>> from hydpy import round_
    >>> round_(rootingdepth.average_values())
    0.3
    """

    mask = whmod_masks.LandTypeSoil()


class SoilTypeParameter(parametertools.ZipParameter):
    """Base class for 1-dimensional soil type-specific parameters.

    We take parameter |AvailableFieldCapacity| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(7)
    >>> landtype(GRASS, GRASS, GRASS, GRASS, GRASS, GRASS, SEALED)
    >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, NONE)
    >>> availablefieldcapacity(
    ...     sand=0.1, sand_cohesive=0.2, loam=0.3, clay=0.4, silt=0.5, peat=0.6
    ... )
    >>> availablefieldcapacity
    availablefieldcapacity(clay=0.4, loam=0.3, peat=0.6, sand=0.1,
                           sand_cohesive=0.2, silt=0.5)
    >>> area(30.0)
    >>> zonearea(6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 9.0)
    >>> from hydpy import round_
    >>> round_(availablefieldcapacity.average_values())
    0.266667
    """

    TYPE = float

    constants = whmod_constants.SOILTYPE_CONSTANTS
    mask = whmod_masks.SoilTypeComplete()

    @property
    def refweights(self):
        """Reference to the associated instance of |ZoneRatio| for calculating areal
        mean values."""
        return self.subpars.pars.control.zonearea


class LanduseMonthParameter(parametertools.KeywordParameter2D):
    """Base class for month- and land type-specific parameters."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    columnnames = parametertools.MonthParameter.entrynames
    rownames = whmod_constants.LANDTYPE_CONSTANTS.sortednames
