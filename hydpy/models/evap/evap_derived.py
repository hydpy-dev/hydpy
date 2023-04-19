# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import objecttools
from hydpy.core import parametertools

# ...from evap
from hydpy.models.evap import evap_control


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class HRUAreaFraction(parametertools.Parameter):
    """The area fraction of each hydrological response unit [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (evap_control.HRUArea,)

    def update(self) -> None:
        r"""Calculate the fractions based on
        :math:`HRUAreaFraction_i = HRUArea_i / \Sigma HRUArea`.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(5)
        >>> hruarea(10.0, 40.0, 20.0, 25.0, 5.0)
        >>> derived.hruareafraction.update()
        >>> derived.hruareafraction
        hruareafraction(0.1, 0.4, 0.2, 0.25, 0.05)
        """
        hruarea = self.subpars.pars.control.hruarea.values
        self.values = hruarea / numpy.sum(hruarea)


class Altitude(parametertools.Parameter):
    """Average (reference) subbasin altitude [100m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    CONTROLPARAMETERS = (
        evap_control.HRUArea,
        evap_control.HRUAltitude,
    )

    def update(self) -> None:
        """Average the individual hydrological response units' altitudes.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(5.0, 3.0, 2.0)
        >>> hrualtitude(1.0, 3.0, 8.0)
        >>> derived.altitude.update()
        >>> derived.altitude
        altitude(3.0)
        """
        control = self.subpars.pars.control
        self.value = numpy.dot(
            control.hruarea.values, control.hrualtitude.values
        ) / numpy.sum(control.hruarea.values)


class Hours(parametertools.HoursParameter):
    """The length of the actual simulation step size in hours [h]."""


class Days(parametertools.DaysParameter):
    """The length of the actual simulation step size in days [d]."""


class NmbLogEntries(parametertools.Parameter):
    """The number of log entries required for a memory duration of 24 hours [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def update(self):
        """Calculate the number of entries and adjust the shape of all relevant log
        sequences.

        The aimed memory duration is one day.  Hence, the required log entries depend
        on the simulation step size:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1h"
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

        >>> pub.timegrids = "2000-01-01 00:00", "2000-01-01 10:00", "5h"
        >>> derived.nmblogentries.update()
        Traceback (most recent call last):
        ...
        ValueError: The value of parameter `nmblogentries` of element `?` cannot be \
determined for a the current simulation step size.  The fraction of the memory period \
(1d) and the simulation step size (5h) leaves a remainder.
        """
        nmb = "1d" / hydpy.pub.timegrids.stepsize
        if nmb % 1:
            raise ValueError(
                f"The value of parameter {objecttools.elementphrase(self)} cannot be "
                f"determined for a the current simulation step size.  The fraction of "
                f"the memory period (1d) and the simulation step size "
                f"({hydpy.pub.timegrids.stepsize}) leaves a remainder."
            )
        self(nmb)
        for seq in self.subpars.pars.model.sequences.logs:
            seq.shape = self
