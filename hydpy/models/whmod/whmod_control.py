# pylint: disable=missing-module-docstring

import itertools

import numpy

from hydpy.core import exceptiontools
from hydpy.core import objecttools
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


class ZoneArea(whmod_parameters.LandTypeCompleteParameter):
    """Zone area [m²]."""

    TIME, SPAN = None, (0.0, None)


class LandType(parametertools.NameParameter):
    """Land cover type [-]."""

    constants = whmod_constants.LANDTYPE_CONSTANTS


class SoilType(parametertools.NameParameter):
    """Soil type [-].

    >>> from hydpy.models.whmod import *
    >>> parameterstep()
    >>> nmbzones(9)
    >>> landtype(GRASS, DECIDUOUS, CORN, CONIFER, SPRINGWHEAT, WINTERWHEAT, SUGARBEETS,
    ...          SEALED, WATER)
    >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, SAND, NONE, NONE)
    >>> soiltype
    soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, SAND, NONE, NONE)
    >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, NONE, NONE, NONE)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `soiltype` of element `?`, \
the following error occurred: The soil type of land type(s) SUGARBEETS must not be NONE.

    >>> soiltype
    soiltype(?)


    >>> soiltype(SAND, SAND_COHESIVE, LOAM, CLAY, SILT, PEAT, SAND, SAND, SAND)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values of parameter `soiltype` of element `?`, \
the following error occurred: The soil type of land type(s) SEALED and WATER must be \
NONE.

    >>> soiltype
    soiltype(?)



    """

    constants = whmod_constants.SOILTYPE_CONSTANTS
    mask = whmod_masks.LandTypeSoil()

    def __call__(self, *args, **kwargs) -> None:

        def _make_names() -> str:
            value2name = whmod_constants.LANDTYPE_CONSTANTS.value2name
            return objecttools.enumeration([value2name[l] for l in landtype[jdxs]])

        try:
            super().__call__(*args, **kwargs)
            landtype = self.subpars.landtype.values
            should_be_soil = (landtype != SEALED) * (landtype != WATER)
            is_soil = self.values != NONE
            if numpy.any(jdxs := should_be_soil * ~is_soil):
                self._valueready = False
                raise ValueError(
                    f"The soil type of land type(s) {_make_names()} must not be NONE."
                )
            if numpy.any(jdxs := ~should_be_soil * is_soil):
                self._valueready = False
                raise ValueError(
                    f"The soil type of land type(s) {_make_names()} must be NONE."
                )
        except BaseException:
            objecttools.augment_excmessage(
                "While trying to set the values of parameter "
                f"{objecttools.elementphrase(self)}"
            )


class InterceptionCapacity(parametertools.KeywordParameter2D):
    """Maximum interception storage [mm]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)

    columnnames = parametertools.MonthParameter.entrynames
    rownames = whmod_constants.LANDTYPE_CONSTANTS.get_sortednames(
        relevant=whmod_masks.LandTypeNonWater.relevant
    )


class DegreeDayFactor(whmod_parameters.LandTypeNonWaterParameter):
    """Degree day factor for snow melting [mm/T/K]."""

    TIME, SPAN = True, (0.0, None)


class AvailableFieldCapacity(whmod_parameters.SoilTypeParameter):
    """Maximum relative soil moisture content [-]."""

    TIME, SPAN = None, (0.0, None)


class RootingDepth(whmod_parameters.LandTypeSoilParameter):
    """Maximum rooting depth [m]."""

    TIME, SPAN = None, (0.0, None)


class GroundwaterDepth(whmod_parameters.SoilTypeParameter):
    """Average groundwater depth [m]."""

    TIME, SPAN = None, (0.0, None)


class WithCapillaryRise(parametertools.Parameter):
    """Flag to turn on/off capillary rise [-]."""

    NDIM, TYPE, TIME = 0, bool, None


class CapillaryThreshold(whmod_parameters.SoilTypeParameter):
    """Relative soil moisture where the capillary rise starts [-]."""

    TIME, SPAN = None, (0.0, None)


class CapillaryLimit(whmod_parameters.SoilTypeParameter):
    """Relative soil moisture where the capillary rise reaches its maximum [-]."""

    TIME, SPAN = None, (0.0, None)


class IrrigationTrigger(parametertools.KeywordParameter2D):
    """Relative soil moisture below which irrigation starts [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)

    columnnames = parametertools.MonthParameter.entrynames
    rownames = whmod_constants.LANDTYPE_CONSTANTS.get_sortednames(
        relevant=whmod_masks.LandTypeSoil.relevant
    )

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim |IrrigationTrigger| following
        :math:`0 \leq IrrigationTrigger \leq IrrigationTarget \leq 1`.

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> trigger = irrigationtrigger

        >>> trigger(
        ...     grass=0.0,
        ...     deciduous=0.0,
        ...     corn=[0.0, 0.0, 0.0, 0.0, 0.0, 0.7, 1.0, 1.3, 0.0, 0.0, 0.0, 0.0],
        ...     conifer=0.0,
        ...     springwheat=0.0,
        ...     winterwheat=0.0,
        ...     sugarbeets=0.0,
        ... )
        >>> trigger.corn_jun, trigger.corn_jul, trigger.corn_aug
        (0.7, 1.0, 1.0)

        >>> irrigationtarget.corn_jun = 0.7
        >>> irrigationtarget.corn_jul = 0.7
        >>> trigger(
        ...     grass=0.0,
        ...     deciduous=0.0,
        ...     corn=[0.0, 0.0, 0.0, 0.0, 0.0, 0.7, 1.0, 1.3, 0.0, 0.0, 0.0, 0.0],
        ...     conifer=0.0,
        ...     springwheat=0.0,
        ...     winterwheat=0.0,
        ...     sugarbeets=0.0,
        ... )
        >>> trigger = irrigationtrigger
        >>> trigger.corn_jun, trigger.corn_jul, trigger.corn_aug
        (0.7, 0.7, 1.0)
        """

        if upper is None:
            upper = self.subpars.irrigationtarget.values.copy()
            upper[numpy.isnan(upper)] = 1.0
        return super().trim(lower, upper)


class IrrigationTarget(parametertools.KeywordParameter2D):
    """Relative soil moisture content at which irrigation ends [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)

    columnnames = parametertools.MonthParameter.entrynames
    rownames = whmod_constants.LANDTYPE_CONSTANTS.get_sortednames(
        relevant=whmod_masks.LandTypeSoil.relevant
    )

    def trim(self, lower=None, upper=None) -> bool:
        r"""Trim |IrrigationTarget| following
        :math:`0 \leq IrrigationTrigger \leq IrrigationTarget \leq 1`.

        >>> from hydpy.models.whmod import *
        >>> parameterstep()
        >>> target = irrigationtarget

        >>> target(
        ...     grass=0.0,
        ...     deciduous=0.0,
        ...     corn=[0.0, 0.0, 0.0, 0.0, 0.0, 0.7, 0.3, -0.1, 0.0, 0.0, 0.0, 0.0],
        ...     conifer=0.0,
        ...     springwheat=0.0,
        ...     winterwheat=0.0,
        ...     sugarbeets=0.0,
        ... )
        >>> target.corn_jun, target.corn_jul, target.corn_aug
        (0.7, 0.3, 0.0)

        >>> irrigationtrigger.corn_jun = 0.7
        >>> irrigationtrigger.corn_jul = 0.7
        >>> target(
        ...     grass=0.0,
        ...     deciduous=0.0,
        ...     corn=[0.0, 0.0, 0.0, 0.0, 0.0, 0.7, 0.3, -0.1, 0.0, 0.0, 0.0, 0.0],
        ...     conifer=0.0,
        ...     springwheat=0.0,
        ...     winterwheat=0.0,
        ...     sugarbeets=0.0,
        ... )
        >>> target = irrigationtarget
        >>> target.corn_jun, target.corn_jul, target.corn_aug
        (0.7, 0.7, 0.0)
        """

        if lower is None:
            lower = self.subpars.irrigationtrigger.values.copy()
            lower[numpy.isnan(lower)] = 0.0
        return super().trim(lower, upper)


class WithExternalIrrigation(parametertools.Parameter):
    """Flag to turn on/off external irrigation [-]."""

    NDIM, TYPE, TIME = 0, bool, None


class BaseflowIndex(whmod_parameters.LandTypeGroundwaterParameter):
    """Baseflow index [-]."""

    TIME, SPAN = None, (0.0, 1.0)


class RechargeDelay(parametertools.Parameter):
    """Delay between soil percolation and groundwater recharge [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)
