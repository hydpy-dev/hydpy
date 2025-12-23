# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools

# ...from snow
from hydpy.models.snow import snow_parameters
from hydpy.models.snow import snow_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""


class GThresh(snow_parameters.Parameter1DLayers):
    """Accumulation threshold [mm]."""

    TIME, SPAN = None, (0.0, None)

    CONTROLPARAMETERS = (
        snow_control.NLayers,
        snow_control.MeanAnSolidPrecip,
        snow_control.CN4,
    )

    def update(self):
        """Update |GThresh| based on :math:`GThresh = MeanAnSolidPrecip / CN4` [-].

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> meanansolidprecip(700.0, 750.0, 730.0, 630.0, 700.0)
        >>> cn4(0.6)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(420.0, 450.0, 438.0, 378.0, 420.0)
        """
        control = self.subpars.pars.control
        self.values = control.meanansolidprecip * control.cn4


class ZMean(parametertools.Parameter):
    """Mean elevation of all layer [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    CONTROLPARAMETERS = (snow_control.ZLayers,)

    def update(self):
        """Update |ZMean| by averaging |ZLayers| (weighted with |LayerArea|).

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> nlayers(5)
        >>> zlayers(700.0, 750.0, 730.0, 630.0, 700.0)
        >>> layerarea(0.1, 0.3, 0.2, 0.2, 0.2)
        >>> derived.zmean.update()
        >>> derived.zmean
        zmean(707.0)
        """
        self.value = self.subpars.pars.control.zlayers.average_values()
