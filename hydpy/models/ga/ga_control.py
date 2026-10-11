# pylint: disable=missing-module-docstring

import hydpy
from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.ga import ga_variables


class NmbSoils(parametertools.NmbParameter):
    """The number of separately modelled soil compartments in the subbasin [-]."""

    SPAN = (1, None)


class NmbBins(parametertools.NmbParameter):
    """The number of available bins for each soil compartment [-].

    Each soil compartment consists of multiple bins.  Bins are the "places" where
    we model individual wetting fronts with different relative moisture values.  Hence,
    |NmbBins| determines the maximum number of wetting fronts we can simulate
    simultaneously.

    The first bin is unique, as it is always "filled" (as if its wetting front covers
    the considered soil column completely).  Hence, for a single 1-front Green & Ampt
    calculation, one must prepare (at least) two bins.  Then, the first bin handles the
    initial soil moisture, while the second bin handles the wetting front's moisture
    and depth.
    """

    SPAN = (2, None)


class DT(parametertools.Parameter):
    """The length of the numerical substeps [T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        """Adjust |DT| when necessary, so the simulation period is an integer multiple.

        Assume we want to perform a simulation over intervals of 30 minutes but define
        |DT| in hours:

        >>> from hydpy.models.ga import *
        >>> simulationstep("30m")
        >>> parameterstep("1h")

        A tenth of an hour then is a fifth of the simulation interval:

        >>> dt(0.1)
        >>> dt
        dt(0.1)
        >>> dt.value
        0.2

        The numerical substeps cannot be longer than the simulation intervals:

        >>> dt(1.0)
        >>> dt
        dt(0.5)

        Zero or negative values are also impossible, of course.  The chosen minimum
        numerical stepsize is one second:

        >>> dt(0.0)
        >>> dt
        dt(0.000278)
        >>> from hydpy import pub
        >>> with pub.options.parameterstep("1s"):
        ...     dt
        dt(1.0)

        When necessary, values within the allowed range are reduced to ensure the
        simulation interval is an integer multiple:

        >>> dt(0.3)
        >>> dt
        dt(0.25)
        """
        max_seconds = int(hydpy.pub.options.simulationstep.seconds)
        act_seconds = min(max(int(round(self.value * max_seconds)), 1), max_seconds)
        if max_seconds % act_seconds == 0.0:
            dt = 1.0 / (max_seconds // act_seconds)
        else:
            dt = 1.0 / (max_seconds // act_seconds + 1)
        return super().trim(lower=dt, upper=dt)


class Sealed(ga_variables.MixinSoils, parametertools.Parameter):
    """Flag indicating if a (soil) compartment is sealed for infiltration [-]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = bool
    SPAN = (False, True)


class SoilArea(ga_variables.MixinSoils, parametertools.Parameter):
    """The area of each soil compartment [km²]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)


class SoilDepth(ga_variables.MixinSoils, parametertools.Parameter):
    """Depth of the considered soil domains [mm]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)


class ResidualMoisture(ga_variables.MixinSoils, parametertools.Parameter):
    """Relative residual water content [-]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, 1.0)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim |ResidualMoisture| following
        :math:`0 \leq ResidualMoisture \leq SaturationMoisture \leq 1`.

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(5)
        >>> residualmoisture(-0.5, 0.0, 0.5, 1.0, 1.5)
        >>> residualmoisture
        residualmoisture(0.0, 0.0, 0.5, 1.0, 1.0)

        >>> saturationmoisture.values = 0.4, 0.5, 0.6, 0.7, 0.8
        >>> residualmoisture(0.6)
        >>> residualmoisture
        residualmoisture(0.4, 0.5, 0.6, 0.6, 0.6)
        """
        if upper is None:
            upper = exceptiontools.getattr_(
                self.subpars.saturationmoisture, "values", None
            )
        return super().trim(lower, upper)


class SaturationMoisture(ga_variables.MixinSoils, parametertools.Parameter):
    """Relative saturation water content [-]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, 1.0)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim |SaturationMoisture| following
        :math:`0 \leq ResidualMoisture \leq SaturationMoisture \leq 1`.

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(5)
        >>> saturationmoisture(-0.5, 0.0, 0.5, 1.0, 1.5)
        >>> saturationmoisture
        saturationmoisture(0.0, 0.0, 0.5, 1.0, 1.0)

        >>> residualmoisture.values = 0.2, 0.3, 0.4, 0.5, 0.6
        >>> saturationmoisture(0.4)
        >>> saturationmoisture
        saturationmoisture(0.4, 0.4, 0.4, 0.5, 0.6)
        """
        if lower is None:
            lower = exceptiontools.getattr_(
                self.subpars.residualmoisture, "values", None
            )
        return super().trim(lower, upper)


class SaturatedConductivity(ga_variables.MixinSoils, parametertools.Parameter):
    """Saturated hydraulic conductivity [mm/T]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)


class PoreSizeDistribution(ga_variables.MixinSoils, parametertools.Parameter):
    """Pore-size distribution parameter [-]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)


class AirEntryPotential(ga_variables.MixinSoils, parametertools.Parameter):
    """Air entry potential [mm]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0.0, None)
