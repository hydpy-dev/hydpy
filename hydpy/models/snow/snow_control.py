# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# from site-packages

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools

# ...from snow


class Z(parametertools.Parameter):
    """Mean subbasin elevation [m]."""
    # todo eigentlich Median der Hypso-Daten und somit überflüssig

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class NSnowLayers(parametertools.Parameter):
    """Number of snow layers  [-].

    Note that |NmbZones| determines the length of the 1-dimensional
    HydPy-GRXJ-Land snow parameters and sequences.  This required that the value of
    the respective |NSnowLayers| instance is set before any of the values
    of these 1-dimensional parameters or sequences are set.  Changing the
    value of the |NSnowLayers| instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.snow import *
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
        old_value = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new_value = self.value

        if new_value != old_value:
            self.subpars.pars.model.parameters.control.meanansolidprecip.shape = (
                new_value
            )
            for der in self.subpars.pars.model.parameters.derived:
                if (der.NDIM > 0) and (der.name not in ("uh1", "uh2")):
                    der.shape = self.value
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
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

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

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


class SnowHyst(parametertools.Parameter):
    """Flag to allow snow hysteries"""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (False, True)


class MeanAnSolidPrecip(parametertools.Parameter):
    """Mean annual solid precipitation [mm/a]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)


class CN1(parametertools.Parameter):
    """weighting coefficient for snow pack thermal state [-]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class CN2(parametertools.Parameter):
    """Degree-day melt coefficient [mm/°C/T]"""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0, None)


class CN3(parametertools.Parameter):
    """Accumulation threshold [mm]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class CN4(parametertools.Parameter):
    """Percentage (between 0 and 1) of annual snowfall defining the melt threshold
    [-]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, 1)
