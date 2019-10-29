# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring
# import...
# ...from HydPy
import hydpy
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.models.evap import evap_control


class DOY(parametertools.DOYParameter):
    """References the "global" day of the year index array [-]."""


class Seconds(parametertools.SecondsParameter):
    """The length of the actual simulation step size in seconds [s]."""


class SCT(parametertools.SCTParameter):
    """References the "global" standard clock time array [-]."""


class UTCLongitude(parametertools.UTCLongitudeParameter):
    """Longitude of the centre of the local time zone [°]."""


class NmbLogEntries(parametertools.Parameter):
    """The number of log entries required for a memory duration of 24 hours
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def update(self):
        """Calculate the number of entries and adjust the shape of all
        relevant log sequences.

        The aimed memory duration is one day.  Hence, the number of the
        required log entries depends on the simulation step size:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2000-01-02', '1h'
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(24)
        >>> for seq in logs:
        ...     print(seq)
        loggedglobalradiation(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                              nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                              nan, nan, nan, nan)
        loggedclearskysolarradiation(nan, nan, nan, nan, nan, nan, nan, nan,
                                     nan, nan, nan, nan, nan, nan, nan, nan,
                                     nan, nan, nan, nan, nan, nan, nan, nan)

        There is an explicit check for inappropriate simulation step sizes:

        >>> pub.timegrids = '2000-01-01 00:00', '2000-01-01 10:00', '5h'
        >>> derived.nmblogentries.update()
        Traceback (most recent call last):
        ...
        ValueError: The value of parameter `nmblogentries` of element `?` \
cannot be determined for a the current simulation step size.  The fraction of \
the memory period (1d) and the simulation step size (5h) leaves a remainder.
        """
        nmb = '1d'/hydpy.pub.timegrids.stepsize
        if nmb % 1:
            raise ValueError(
                f'The value of parameter {objecttools.elementphrase(self)} '
                f'cannot be determined for a the current simulation step '
                f'size.  The fraction of the memory period (1d) and the '
                f'simulation step size ({hydpy.pub.timegrids.stepsize}) '
                f'leaves a remainder.'
            )
        self(nmb)
        for seq in self.subpars.pars.model.sequences.logs:
            seq.shape = self


class LatitudeRad(parametertools.Parameter):
    """The latitude [rad]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (-1.5708, 1.5708)

    CONTROLPARAMETERS = (
        evap_control.Latitude,
    )

    def update(self):
        """Update |LatitudeRad| based on parameter |Latitude|.

        >>> from hydpy import round_
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> for value in (-90.0, -45.0, 0.0, 45.0, 90.0):
        ...     latitude(value)
        ...     derived.latituderad.update()
        ...     round_(latitude.value, end=': ')
        ...     round_(derived.latituderad.value)
        -90.0: -1.570796
        -45.0: -0.785398
        0.0: 0.0
        45.0: 0.785398
        90.0: 1.570796
        """
        self.value = 3.141592653589793/180.*self.subpars.pars.control.latitude
