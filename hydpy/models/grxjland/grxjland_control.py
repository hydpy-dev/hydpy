# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# from site-packages

# ...from HydPy
from hydpy.core import parametertools

# ...from grxjland


class Area(parametertools.Parameter):
    """Subbasin area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class Z(parametertools.Parameter):
    """Mean subbasin elevation [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NSnowLayers(parametertools.Parameter):
    """Number of snow layers  [-].

    Note that |NmbZones| determines the length of the 1-dimensional
    HydPy-GRXJ-Land snow parameters and sequences.  This required that the value of
    the respective |NSnowLayers| instance is set before any of the values
    of these 1-dimensional parameters or sequences are set.  Changing the
    value of the |NSnowLayers| instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.grxjland import *
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, 101)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to |NmbZones| instances within
        parameter control files.  Sets the shape of most 1-dimensional
        snow parameter objects and sequence objects
        additionally.
        """
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.parameters.control.meanansolidprecip.shape = self.value
        for der in self.subpars.pars.model.parameters.derived:
            if (der.NDIM > 0) and (der.name not in ("uh1", "uh2")):
                der.shape = self.value
        for seq in self.subpars.pars.model.sequences.fluxes:
            if seq.NDIM > 0:
                seq.shape = self.value
        for seq in self.subpars.pars.model.sequences.inputs:
            if seq.NDIM > 0:
                seq.shape = self.value
        for seq in self.subpars.pars.model.sequences.states:
            if seq.NDIM > 0:
                seq.shape = self.value


class HypsoData(parametertools.Parameter):
    """Array of length 101 : min, q01 to q99 and max of catchment elevation
    distribution [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of HypsoData to 101"""
        self.shape = 101
        super().__call__(*args, **kwargs)


class GradTMean(parametertools.Parameter):
    """Array of length 366 : gradient of daily mean temperature for each day of year
    [°C/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of HypsoData to 366"""
        self.shape = 366
        super().__call__(*args, **kwargs)


class GradTMin(parametertools.Parameter):
    """Array of length 366 : gradient of daily minimum temperature for each day of
    year [°C/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of HypsoData to 366"""
        self.shape = 366
        super().__call__(*args, **kwargs)


class GradTMax(parametertools.Parameter):
    """Array of length 366 : elevation gradient of daily maximum temperature for each
    day of year [°C/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of HypsoData to 366"""
        self.shape = 366
        super().__call__(*args, **kwargs)


class MeanAnSolidPrecip(parametertools.Parameter):
    """Mean annual solid precipitation [mm/a]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)


class CN1(parametertools.Parameter):
    """weighting coefficient for snow pack thermal state [-]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class CN2(parametertools.Parameter):
    """Degree-day melt coefficient [mm/°C/d]"""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0, None)


class CN3(parametertools.Parameter):
    """Accumulation threshold [mm]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class CN4(parametertools.Parameter):
    """Percentage (between 0 and 1) of annual snowfall defining the melt threshold
    [-]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, 1)


class X1(parametertools.Parameter):
    """Maximum capacity of the production storage [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class X2(parametertools.Parameter):
    """groundwater exchange coefficient [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class X3(parametertools.Parameter):
    """One timestep ahead maximum capacity of the routing store [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class X4(parametertools.Parameter):
    """Time base of unit hydrographs UH1 (X4) and UH2 (2*X4) [d]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.5, None)


class X5(parametertools.Parameter):
    """Intercatchment exchange threshold [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class X6(parametertools.Parameter):
    """coefficient for emptying exponential store [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)
