# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import parametertools


class NmbSoils(parametertools.Parameter):
    """The number of separately modelled soil compartments in the subbasin [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs) -> None:
        nmbsoils_old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        nmbsoils_new = self.value
        if nmbsoils_new != nmbsoils_old:
            nmbbins = exceptiontools.getattr_(self.subpars.nmbbins, "value", None)
            for subpars in self.subpars.pars:
                for par in subpars:
                    if par.NDIM == 1:
                        par.shape = nmbsoils_new
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.shape = nmbsoils_new
                    elif (seq.NDIM == 2) and (nmbbins is not None):
                        seq.shape = nmbbins, nmbsoils_new


class NmbBins(parametertools.Parameter):
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

    NDIM, TYPE, TIME, SPAN = 0, int, None, (2, None)

    def __call__(self, *args, **kwargs) -> None:
        nmbbins_old = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        nmbbins_new = self.value
        if nmbbins_new != nmbbins_old:
            nmbsoils = exceptiontools.getattr_(self.subpars.nmbsoils, "value", None)
            if nmbsoils is not None:
                for subseqs in self.subpars.pars.model.sequences:
                    for seq in subseqs:
                        if seq.NDIM == 2:
                            seq.shape = nmbbins_new, nmbsoils


class DT(parametertools.Parameter):
    """The length of the numerical substeps [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (None, None)

    def trim(self, lower=None, upper=None) -> bool:
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


class Sealed(parametertools.Parameter):
    """Flag indicating if a (soil) compartment is sealed for infiltration [-]."""

    NDIM, TYPE, TIME, SPAN = 1, bool, None, (False, True)


class SoilArea(parametertools.Parameter):
    """The area of each soil compartment [km²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class SoilDepth(parametertools.Parameter):
    """Depth of the considered soil domains [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class ResidualMoisture(parametertools.Parameter):
    """Relative residual water content [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    def trim(self, lower=None, upper=None) -> bool:
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


class SaturationMoisture(parametertools.Parameter):
    """Relative saturation water content [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    def trim(self, lower=None, upper=None) -> bool:
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


class SaturatedConductivity(parametertools.Parameter):
    """Saturated hydraulic conductivity [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)


class PoreSizeDistribution(parametertools.Parameter):
    """Pore-size distribution parameter [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class AirEntryPotential(parametertools.Parameter):
    """Air entry potential [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
