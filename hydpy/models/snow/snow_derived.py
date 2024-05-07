# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools

# ...from snow
from hydpy.models.snow import snow_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""


class GThresh(parametertools.Parameter):
    """Accumulation threshold [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    strict_valuehandling = False

    CONTROLPARAMETERS = (
        snow_control.MeanAnSolidPrecip,
        snow_control.CN4,
        snow_control.NLayers,
    )

    def update(self):
        """Update |GThresh| based on mean annual solid precipitation
        |MeanAnSolidPrecip| and the percentage of annual snowfall |CN4| defining the
        melt threshold [-].

        >>> from hydpy.models.snow import *
        >>> parameterstep('1d')
        >>> nlayers(5)
        >>> meanansolidprecip(700., 750., 730., 630., 700.)
        >>> cn4(0.6)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(420.0, 450.0, 438.0, 378.0, 420.0)
        """
        con = self.subpars.pars.control.fastaccess
        self.shape = con.nlayers
        gthresh = numpy.array(con.meanansolidprecip) * con.cn4
        self(gthresh)
