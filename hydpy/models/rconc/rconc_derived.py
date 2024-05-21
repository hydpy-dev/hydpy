# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools

# ...from evap
from hydpy.models.rconc import rconc_control


class KSC(parametertools.Parameter):
    """Coefficient of the individual storages of the linear storage cascade [1/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)

    CONTROLPARAMETERS = (rconc_control.RetentionTime, rconc_control.NmbStorages)

    def update(self):
        """Update |KSC| based on
        :math:`KSC = \\frac{2 \\cdot NmbStorages}{RetentionTime}`.

        >>> from hydpy.models.rconc import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> retentiontime(8.0)
        >>> nmbstorages(2.0)
        >>> derived.ksc.update()
        >>> derived.ksc
        ksc(0.5)

        >>> retentiontime(0.0)
        >>> nmbstorages(2.0)
        >>> derived.ksc.update()
        >>> derived.ksc
        ksc(inf)
        """
        control = self.subpars.pars.control
        if control.retentiontime.value <= 0.0:
            self.value = numpy.inf
        else:
            self.value = 2.0 * control.nmbstorages.value / control.retentiontime.value


class DT(parametertools.Parameter):
    """Relative length of each simulation step [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (rconc_control.NmbSteps,)

    def update(self):
        """Update |DT| based on :math:`DT = \\frac{1}{NmbSteps}`.

        >>> from hydpy.models.rconc import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nmbsteps(2.0)
        >>> derived.dt.update()
        >>> derived.dt
        dt(1.0)
        >>> nmbsteps(10.0)
        >>> derived.dt.update()
        >>> derived.dt
        dt(0.2)

        Note that the value assigned to parameter |NmbSteps| depends on the current
        parameter step size (one day).  Due to the current simulation step size (one
        hour), the applied |NmbSteps| value is five:

        >>> nmbsteps.value
        5
        """
        self(1.0 / self.subpars.pars.control.nmbsteps)
