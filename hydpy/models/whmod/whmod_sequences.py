# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools

from hydpy.models.whmod import whmod_masks


class Mixin1DSequence(sequencetools.Sequence_):
    """Mixin class for all 1-dimensional sequences."""

    NDIM, NUMERIC = 1, False

    @property
    def refweights(self):
        """Reference to the associated instance of |ZoneRatio| for calculating areal
        mean values."""
        return self.subseqs.seqs.model.parameters.derived.zoneratio


class Factor1DSoilSequence(Mixin1DSequence, sequencetools.FactorSequence):
    """Base class for 1-dimensional factors sequences relevant to all soil zones.

    We take class |RelativeSoilMoisture| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> factors.relativesoilmoisture = 1.0, 3.0, 1.5, 3.5, 2.0, 2.5, 0.5, nan, nan
    >>> from hydpy import round_
    >>> round_(factors.relativesoilmoisture.average_values())
    1.928571
    """

    mask = whmod_masks.LandTypeSoil()


class Flux1DCompleteSequence(Mixin1DSequence, sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences relevant to all zones.

    We take class |TotalEvapotranspiration| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> fluxes.totalevapotranspiration = 1.0, 3.0, 1.5, 3.5, 2.0, 2.5, 0.5, 0.0, 5.0
    >>> from hydpy import round_
    >>> round_(fluxes.totalevapotranspiration.average_values())
    2.2
    """

    mask = whmod_masks.LandTypeComplete()


class FluxSequence1DWaterSequence(Mixin1DSequence, sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences relevant to all water zones.

    We take class |LakeEvaporation| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(10)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 27.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> fluxes.lakeevaporation = nan, nan, nan, nan, nan, nan, nan, nan, 2.0, 4.0
    >>> from hydpy import round_
    >>> round_(fluxes.lakeevaporation.average_values())
    3.5
    """

    mask = whmod_masks.LandTypeWater()


class Flux1DNonWaterSequence(Mixin1DSequence, sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences relevant to all land zones.

    We take class |Throughfall| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> fluxes.throughfall = 1.0, 3.0, 1.5, 3.5, 2.0, 2.5, 0.5, 0.0, nan
    >>> from hydpy import round_
    >>> round_(fluxes.throughfall.average_values())
    1.5
    """

    mask = whmod_masks.LandTypeNonWater()


class Flux1DSoilSequence(Mixin1DSequence, sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences relevant to all soil zones.

    We take class |Percolation| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> fluxes.percolation = 1.0, 3.0, 1.5, 3.5, 2.0, 2.5, 0.5, nan, nan
    >>> from hydpy import round_
    >>> round_(fluxes.percolation.average_values())
    1.928571
    """

    mask = whmod_masks.LandTypeSoil()


class Flux1DGroundwaterSequence(Mixin1DSequence, sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences relevant to all groundwater zones.

    We take class |Baseflow| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> fluxes.baseflow = 1.0, 3.0, 1.5, 3.5, 2.0, 2.5, 0.5, nan, 5.0
    >>> from hydpy import round_
    >>> round_(fluxes.baseflow.average_values())
    2.675676
    """

    mask = whmod_masks.LandTypeGroundwater()


class State1DNonWaterSequence(Mixin1DSequence, sequencetools.StateSequence):
    """Base class for 1-dimensional state sequences relevant to all land zones.

    We take class |InterceptedWater| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> states.interceptedwater = 1.0, 3.0, 1.5, 3.5, 2.0, 2.5, 0.5, 0.0, nan
    >>> from hydpy import round_
    >>> round_(states.interceptedwater.average_values())
    1.5
    """

    mask = whmod_masks.LandTypeNonWater()


class State1DSoilSequence(Mixin1DSequence, sequencetools.StateSequence):
    """Base class for 1-dimensional state sequences relevant to all soil zones.

    We take class |SoilMoisture| as an example:

    >>> from hydpy.models.whmod import *
    >>> parameterstep("1d")
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> zonearea(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    >>> area(sum(zonearea))
    >>> derived.zoneratio.update()
    >>> states.soilmoisture = 1.0, 3.0, 1.5, 3.5, 2.0, 2.5, 0.5, nan, nan
    >>> from hydpy import round_
    >>> round_(states.soilmoisture.average_values())
    1.928571
    """

    mask = whmod_masks.LandTypeSoil()
