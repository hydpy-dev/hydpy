# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
from __future__ import annotations

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.evap import evap_parameters


class NmbHRU(parametertools.Parameter):
    """The number of separately modelled hydrological response units [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def __call__(self, *args, **kwargs) -> None:
        nmbhru_old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        nmbhru_new = self.value
        if nmbhru_new != nmbhru_old:
            for subpars in self.subpars.pars:
                for par in subpars:
                    if (par.NDIM == 1) and not isinstance(
                        par, parametertools.KeywordParameter1D
                    ):
                        par.shape = nmbhru_new
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.shape = nmbhru_new


class HRUType(parametertools.NameParameter):
    """Hydrological response unit type [-]."""

    NDIM, TYPE, TIME = 1, int, None
    SPAN = (None, None)
    constants = parametertools.Constants(ANY=0)


class Water(evap_parameters.ZipParameter1D):
    """A flag that indicates whether the individual zones are water areas or not."""

    TYPE, TIME, SPAN = bool, None, (False, True)


class Interception(evap_parameters.ZipParameter1D):
    """A flag that indicates whether interception evaporation is relevant for the
    individual zones."""

    TYPE, TIME, SPAN = bool, None, (False, True)


class Soil(evap_parameters.ZipParameter1D):
    """A flag that indicates whether soil evapotranspiration is relevant for the
    individual zones."""

    TYPE, TIME, SPAN = bool, None, (False, True)


class Plant(evap_parameters.ZipParameter1D):
    """A flag that indicates whether the individual zones contain any vegetation."""

    TYPE, TIME, SPAN = bool, None, (False, True)


class Tree(evap_parameters.ZipParameter1D):
    """A flag that indicates whether the individual zones contain tree-like
    vegetation."""

    TYPE, TIME, SPAN = bool, None, (False, True)


class Conifer(evap_parameters.ZipParameter1D):
    """A flag that indicates whether the individual zones contain conifer-like
    vegetation."""

    TYPE, TIME, SPAN = bool, None, (False, True)


class HRUArea(parametertools.Parameter):
    """The area of each hydrological response unit [km²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class HRUAltitude(evap_parameters.ZipParameter1D):
    """The altitude of each hydrological response unit [m]."""

    TYPE, TIME, SPAN = float, None, (None, None)
    INIT = 0.0


class MeasuringHeightWindSpeed(parametertools.Parameter):
    """The height above ground of the wind speed measurements [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)
    INIT = 10.0


class AirTemperatureAddend(evap_parameters.ZipParameter1D):
    """Adjustment addend for air temperature [K]."""

    TYPE, TIME, SPAN = float, None, (None, None)
    INIT = 0.0


class CoastFactor(evap_parameters.ZipParameter1D):
    """The "coast factor" of Turc-Wendling's reference evapotranspiration equation
    [-]."""

    TYPE, TIME, SPAN = float, None, (0.6, 1.0)
    INIT = 1.0


class Albedo(evap_parameters.LandMonthParameter):
    """Earth surface albedo [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.5


class GroundAlbedo(evap_parameters.ZipParameter1D):
    """The albedo of the snow-free ground (including soils, sealed surfaces, and water
    areas) [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.2


class GroundAlbedoSnow(evap_parameters.ZipParameter1D):
    """The albedo of the snow-covered ground (including soils and sealed surfaces)
    [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.8


class LeafAlbedo(evap_parameters.PlantParameter1D):
    """The albedo of the snow-free leaves [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.2


class LeafAlbedoSnow(evap_parameters.PlantParameter1D):
    """The albedo of the snow-covered leaves [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, 1.0)
    INIT = 0.8


class LeafAreaIndex(evap_parameters.LandMonthParameter):
    """Leaf area index [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 5.0


class CropHeight(evap_parameters.LandMonthParameter):
    """Crop height [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 1.0


class CloudTypeFactor(parametertools.Parameter):
    """Cloud type-specific factor for calculating atmospheric longwave counter radiation
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.2


class NightCloudFactor(parametertools.Parameter):
    """Factor for adjusting daytime estimates of the cloud coverage degree to nighttime
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.0


class Emissivity(parametertools.Parameter):
    """The emissivity of the land surface [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.95


class AverageSoilHeatFlux(parametertools.MonthParameter):
    """Monthly averages of the soil heat flux [W/m²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


class SurfaceResistance(evap_parameters.LandMonthParameter):
    """Surface resistance of water areas, sealed areas, and vegetation with sufficient
    water supply [s/m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 100.0


class WetSoilResistance(evap_parameters.SoilParameter1D):
    """Surface resistance of wet soils [s/m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 100.0


class SoilResistanceIncrease(evap_parameters.SoilParameter1D):
    """Increase in soil surface resistance if evaporation dominates precipitation
    [s/m/T]."""

    TYPE, TIME, SPAN = float, True, (0.0, None)
    INIT = 0.0


class WetnessThreshold(evap_parameters.SoilParameter1D):
    """The ratio between precipitation and potential evapotranspiration above which the
    topmost soil layer becomes wet [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 1.0


class LeafResistance(evap_parameters.PlantParameter1D):
    """Surface resistance of plant leaves [s/m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 100.0


class EvapotranspirationFactor(evap_parameters.ZipParameter1D):
    """The adjustment factor for potential evapotranspiration [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 1.0


class MonthFactor(parametertools.MonthParameter):
    """Factor for converting general potential evaporation or evapotranspiration
    (usually grass reference evapotranspiration) to month-specific potential
    evaporation or evapotranspiration [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class LandMonthFactor(evap_parameters.LandMonthParameter):
    """Factor for converting general potential evaporation or evapotranspiration
    (usually grass reference evapotranspiration) to land-use- and month-specific
    potential evaporation or evapotranspiration [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)


class AltitudeFactor(evap_parameters.ZipParameter1D):
    """Decrease of potential evapotranspiration with altitude [-1/100m].

    In the terminology of HBV96: ECAlt."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.1


class PrecipitationFactor(evap_parameters.ZipParameter1D):
    """Decrease in potential evapotranspiration due to precipitation [T/mm].

    In the terminology of HBV96: EPF.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, False, (0.0, None)
    INIT = 0.0


class AirTemperatureFactor(evap_parameters.ZipParameter1D):
    """Temperature factor related to the difference of current reference
    evapotranspiration and normal reference evapotranspiration [1/°C].

    In the terminology of HBV96: ETF.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.1


class TemperatureThresholdIce(evap_parameters.WaterParameter1D):
    """Temperature threshold for evaporation from water areas [°C].

    In the terminology of HBV96: TTIce.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class MaxSoilWater(evap_parameters.SoilParameter1D):
    """Maximum soil water content [mm].

    In the terminology of HBV96: FC.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 200.0

    def trim(self, lower=None, upper=None) -> None:
        r"""Trim values in accordance with
        :math:`WiltingPoint \leq FieldCapacity \leq MaxSoilWater`.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> wiltingpoint(20.0)
        >>> maxsoilwater(10.0, 50.0, 90.0)
        >>> maxsoilwater
        maxsoilwater(20.0, 50.0, 90.0)

        >>> fieldcapacity.values = 60.0
        >>> maxsoilwater.trim()
        >>> maxsoilwater
        maxsoilwater(60.0, 60.0, 90.0)
        """
        if lower is None:
            p = self.subpars
            if (fc := getattr(p, "fieldcapacity", None)) is not None:
                lower = exceptiontools.getattr_(fc, "value", None)
            if lower is None and (wp := getattr(p, "wiltingpoint", None)) is not None:
                lower = exceptiontools.getattr_(wp, "value", None)
        super().trim(lower, upper)


class FieldCapacity(evap_parameters.SoilParameter1D):
    """Field capacity [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 100.0

    def trim(self, lower=None, upper=None) -> None:
        r"""Trim values in accordance with
        :math:`WiltingPoint \leq FieldCapacity \leq MaxSoilWater`.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> wiltingpoint(20.0)
        >>> maxsoilwater(80.0)
        >>> fieldcapacity(10.0, 50.0, 90.0)
        >>> fieldcapacity
        fieldcapacity(20.0, 50.0, 80.0)
        """
        if lower is None:
            if (wp := getattr(self.subpars, "wiltingpoint", None)) is not None:
                lower = exceptiontools.getattr_(wp, "value", None)
        if upper is None:
            if (msw := getattr(self.subpars, "maxsoilwater", None)) is not None:
                upper = exceptiontools.getattr_(msw, "value", None)
        super().trim(lower, upper)


class WiltingPoint(evap_parameters.SoilParameter1D):
    """Permanent wilting point [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 50.0

    def trim(self, lower=None, upper=None) -> None:
        r"""Trim values in accordance with
        :math:`WiltingPoint \leq FieldCapacity \leq MaxSoilWater`.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> maxsoilwater(100.0)
        >>> wiltingpoint(-10.0, 50.0, 110.0)
        >>> wiltingpoint
        wiltingpoint(0.0, 50.0, 100.0)

        >>> fieldcapacity.values = 80.0
        >>> wiltingpoint.trim()
        >>> wiltingpoint
        wiltingpoint(0.0, 50.0, 80.0)
        """
        if upper is None:
            p = self.subpars
            if (fc := getattr(p, "fieldcapacity", None)) is not None:
                upper = exceptiontools.getattr_(fc, "value", None)
            if upper is None and (msw := getattr(p, "maxsoilwater", None)) is not None:
                upper = exceptiontools.getattr_(msw, "value", None)
        super().trim(lower, upper)


class SoilMoistureLimit(evap_parameters.SoilParameter1D):
    """Relative soil moisture limit for potential evapotranspiration [-].

    In the terminology of HBV96: LP.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    INIT = 0.9


class ExcessReduction(evap_parameters.SoilParameter1D):
    """A factor for restricting actual to potential evapotranspiration [-].

    In the terminology of HBV96: ERED.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


class DisseFactor(evap_parameters.SoilParameter1D):
    """Factor for calculating actual soil evapotranspiration based on potential
    evapotranspiration estimates following the :cite:t:`ref-Disse1995` formulation of
    the :cite:t:`ref-Minhas1974` equation.

    In the terminology of :cite:t:`ref-Minhas1974` and :cite:t:`ref-Disse1995`: r.

    In the terminology of LARSIM: GRASREF_R.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 5.0
