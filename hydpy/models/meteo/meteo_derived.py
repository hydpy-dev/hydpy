# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.models.meteo import meteo_fixed
from hydpy.models.meteo import meteo_control


class DOY(parametertools.DOYParameter):
    """References the "global" day of the year index array [-]."""


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class Seconds(parametertools.SecondsParameter):
    """The length of the actual simulation step size in seconds [s]."""


class Hours(parametertools.HoursParameter):
    """The length of the actual simulation step size in hours [h]."""


class Days(parametertools.DaysParameter):
    """The length of the actual simulation step size in days [d]."""


class SCT(parametertools.SCTParameter):
    """References the "global" standard clock time array [h]."""


class NmbLogEntries(parametertools.Parameter):
    """The number of log entries required for memorising one day's data [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def update(self):
        """Calculate the number of entries and adjust the shape of all relevant log
        sequences.

        The aimed memory duration is always one day.  Hence, the number of the required
        log entries depends on the simulation step size:

        >>> from hydpy.models.meteo import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1h"
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(24)
        >>> logs  # doctest: +ELLIPSIS
        loggedsunshineduration(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan)
        ...

        To prevent losing information, updating parameter |NmbLogEntries| resets the
        shape of the relevant log sequences only when necessary:

        >>> logs.loggedsunshineduration = 1.0
        >>> derived.nmblogentries(24)
        >>> logs  # doctest: +ELLIPSIS
        loggedsunshineduration(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                               1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                               1.0, 1.0, 1.0, 1.0)
        ...

        There is an explicit check for inappropriate simulation step sizes:

        >>> pub.timegrids = "2000-01-01 00:00", "2000-01-01 10:00", "5h"
        >>> derived.nmblogentries.update()
        Traceback (most recent call last):
        ...
        ValueError: The value of parameter `nmblogentries` of element `?` cannot be \
determined for a the current simulation step size.  The fraction of the memory period \
(1d) and the simulation step size (5h) leaves a remainder.

        .. testsetup::

            >>> del pub.timegrids
        """
        nmb = "1d" / hydpy.pub.options.simulationstep
        if nmb % 1:
            raise ValueError(
                f"The value of parameter {objecttools.elementphrase(self)} cannot be "
                f"determined for a the current simulation step size.  The fraction of "
                f"the memory period (1d) and the simulation step size "
                f"({hydpy.pub.timegrids.stepsize}) leaves a remainder."
            )
        self(nmb)
        nmb = int(nmb)
        for seq in self.subpars.pars.model.sequences.logs:
            shape = exceptiontools.getattr_(seq, "shape", (None,))
            if nmb != shape[-1]:
                seq.shape = nmb


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
