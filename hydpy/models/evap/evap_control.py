# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class Latitude(parametertools.Parameter):
    """The latitude [decimal degrees]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (-90., 90.)


class Longitude(parametertools.Parameter):
    """The longitude [decimal degrees]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (-180., 180.)


class MeasuringHeightWindSpeed(parametertools.Parameter):
    """The height above ground of the wind speed measurements [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class AngstromConstant(parametertools.Parameter):
    """The Ångström "a" coefficient for calculating global radiation [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

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
            upper = getattr(self.subpars.angstromfactor, 'value', None)
            if upper is None:
                upper = 1.
            else:
                upper = 1. - upper
        super().trim(lower, upper)


class AngstromFactor(parametertools.Parameter):
    """The Ångström "b" coefficient for calculating global radiation [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

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
            upper = getattr(self.subpars.angstromconstant, 'value', None)
            if upper is None:
                upper = 1.
            else:
                upper = 1. - upper
        super().trim(lower, upper)
