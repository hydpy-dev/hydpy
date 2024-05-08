# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# from site-packages

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import parametertools

# ...from snow


class NLayers(parametertools.Parameter):
    """Number of snow layers  [-].

    Note that |NLayers| determines the length of the 1-dimensional
    HydPy-Snow parameters and sequences.  This requires that the value of
    the respective |NLayers| instance is set before any of the values
    of these 1-dimensional parameters or sequences are set.  Changing the
    value of the |NLayers| instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep('1d')
        >>> nlayers(5)
        >>> meanansolidprecip.shape
        (5,)
        >>> layerarea.shape
        (5,)
        >>> derived.gthresh.shape
        (5,)
    """

    # todo Muss Länge mit 101 begrenzt sein?
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
            for subpars in self.subpars.pars.model.parameters:
                for par in subpars:
                    if (par.NDIM > 0) and (
                        par.name not in ("gradtmean", "gradtmin", "gradtmax")
                    ):
                        par.shape = new_value
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM > 0:
                        seq.shape = self.value


class ZLayers(parametertools.Parameter):
    """Height of each snow layer [m]

    The height for each snow layer can be set directly:

    >>> from hydpy.models.snow import *
    >>> parameterstep("1d")
    >>> nlayers(5)
    >>> zlayers(400.0, 1000.0, 2000.0, 3000.0, 4000.0)
    >>> zlayers
    zlayers(400.0, 1000.0, 2000.0, 3000.0, 4000.0)
    >>> layerarea(0.2, 0.2, 0.2, 0.1, 0.3)
    >>> zlayers.average_values()
    2180.0
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0

    @property
    def refweights(self):
        """Weights for calculating mean."""
        return self.subpars.layerarea


class LayerArea(parametertools.Parameter):
    """Area of snow layer as a percentage of total area [-]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


class GradP(parametertools.Parameter):
    """Altitude gradient precipitation [1/m]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 0.00041


class GradTMean(parametertools.Parameter):
    """Array of length 366 : gradient of daily mean temperature for each day of year
    [°C/100m]."""

    # todo Monatswerte oder doy ?
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of GradTMean to 366"""
        self.shape = 366
        super().__call__(*args, **kwargs)


class GradTMin(parametertools.Parameter):
    """Array of length 366 : gradient of daily minimum temperature for each day of
    year [°C/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of GradTMin to 366"""
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
    """Degree-day melt coefficient [mm/°C/T]"""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0, None)


class CN3(parametertools.Parameter):
    """Accumulation threshold [mm]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class CN4(parametertools.Parameter):
    """Percentage (between 0 and 1) of annual snowfall defining the melt threshold
    [-]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, 1)


class Hysteresis(parametertools.Parameter):
    """Hysteresis of build-up and melting of the snow cover [-]"""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (None, None)
    INIT = False
