# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.meteo import meteo_fixed
from hydpy.models.meteo import meteo_control


class DOY(parametertools.DOYParameter):
    """References the "global" day of the year index array [-]."""


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class Seconds(parametertools.SecondsParameter):
    """The length of the actual simulation step size in seconds [s]."""


class SCT(parametertools.SCTParameter):
    """References the "global" standard clock time array [h]."""


class UTCLongitude(parametertools.UTCLongitudeParameter):
    """Longitude of the centre of the local time zone [°]."""


class LatitudeRad(parametertools.Parameter):
    """The latitude [rad]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (-1.5708, 1.5708)

    FIXEDPARAMETERS = (meteo_fixed.Pi,)
    CONTROLPARAMETERS = (meteo_control.Latitude,)

    def update(self):
        """Update |LatitudeRad| based on parameter |Latitude|.

        >>> from hydpy import round_
        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> for value in (-90.0, -45.0, 0.0, 45.0, 90.0):
        ...     latitude(value)
        ...     derived.latituderad.update()
        ...     round_(latitude.value, end=": ")
        ...     round_(derived.latituderad.value)
        -90.0: -1.570796
        -45.0: -0.785398
        0.0: 0.0
        45.0: 0.785398
        90.0: 1.570796
        """
        pars = self.subpars.pars
        self.value = pars.fixed.pi / 180.0 * pars.control.latitude
