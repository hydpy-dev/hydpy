# pylint: disable=missing-module-docstring

import numpy

import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.statcorr import statcorr_control


class IsForecastMode(parametertools.Parameter):
    """Flag telling whether |Options.simulationmode| currently is `forecast` [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool

    def update(self) -> None:
        """Take the current value of |Options.simulationmode| from module |pub|.

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> derived.isforecastmode.update()
        >>> derived.isforecastmode
        isforecastmode(False)

        >>> pub.options.simulationmode = "forecast"
        >>> derived.isforecastmode.update()
        >>> derived.isforecastmode
        isforecastmode(True)

        >>> del pub.options.simulationmode
        """
        self(hydpy.pub.options.simulationmode == "forecast")


class NmbLogEntries(parametertools.Parameter):
    """The number of log entries required for memorising the data for the
    logging window [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = int
    SPAN = (1, None)
    CONTROLPARAMETERS = (statcorr_control.LoggingWindow,)

    def update(self) -> None:
        """Calculate the number of entries and adjust the shape of all relevant log
        sequences.

        The number of the required log entries depends on the
        parameter |LoggingWindow| and the simulation step size:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> from hydpy.core.timetools import Period
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1h"
        >>> loggingwindow(24)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(24)
        >>> logs  # doctest: +ELLIPSIS
        loggedobserveddischarge(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                nan, nan, nan, nan)
        loggedsimulateddischarge(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan)

        To prevent losing information, updating parameter |NmbLogEntries| resets the
        shape of the relevant log sequences only when necessary:

        >>> logs.loggedobserveddischarge = 1.0
        >>> derived.nmblogentries(24)
        >>> logs  # doctest: +ELLIPSIS
        loggedobserveddischarge(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0, 1.0)
        loggedsimulateddischarge(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                                 nan, nan, nan, nan)

        .. testsetup::

            >>> del pub.timegrids
        """
        control = self.subpars.pars.control

        nmb = control.loggingwindow.value
        self(nmb)
        nmb = int(nmb)
        for seq in self.subpars.pars.model.sequences.logs:
            shape = exceptiontools.getattr_(seq, "shape", (None,))
            if nmb != shape[-1]:
                seq.shape = nmb
