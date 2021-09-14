# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools


class Latitude(parametertools.Parameter):
    """The latitude [decimal degrees]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (-90.0, 90.0)


class Longitude(parametertools.Parameter):
    """The longitude [decimal degrees]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (-180.0, 180.0)


class MeasuringHeightWindSpeed(parametertools.Parameter):
    """The height above ground of the wind speed measurements [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class AngstromConstant(parametertools.MonthParameter):
    """The Ångström "a" coefficient for calculating global radiation [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 0.25

    def trim(self, lower=None, upper=None):
        """Trim values following :math:`AngstromConstant \\leq  1 -
        AngstromFactor` or at least following :math:`AngstromConstant \\leq  1`.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> angstromconstant(1.5)
        >>> angstromconstant
        angstromconstant(1.0)
        >>> angstromfactor.value = 0.6
        >>> angstromconstant(0.5)
        >>> angstromconstant
        angstromconstant(0.4)
        """
        if upper is None:
            upper = self.subpars.angstromfactor.values.copy()
            idxs = numpy.isnan(upper)
            upper[idxs] = 1.0
            upper[~idxs] = 1.0 - upper[~idxs]
        super().trim(lower, upper)


class AngstromFactor(parametertools.MonthParameter):
    """The Ångström "b" coefficient for calculating global radiation [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)
    INIT = 0.5

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`AngstromFactor \\leq  1 -
        AngstromConstant` or at least in accordance with :math:`AngstromFactor
        \\leq  1`.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> angstromfactor(1.5)
        >>> angstromfactor
        angstromfactor(1.0)
        >>> angstromconstant.value = 0.6
        >>> angstromfactor(0.5)
        >>> angstromfactor
        angstromfactor(0.4)
        """
        if upper is None:
            upper = self.subpars.angstromconstant.values.copy()
            idxs = numpy.isnan(upper)
            upper[idxs] = 1.0
            upper[~idxs] = 1.0 - upper[~idxs]
        super().trim(lower, upper)
