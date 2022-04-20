# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
import hydpy
from hydpy.core import objecttools
from hydpy.core import parametertools


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
