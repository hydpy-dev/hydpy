# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import parametertools

# ...from snow
from hydpy.models.grxjland import grxjland_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""


class UH1(parametertools.Parameter):
    """Unit hydrograph UH1 ordinates [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling = False

    CONTROLPARAMETERS = (grxjland_control.X4,)

    def update(self):
        """Update |UH1| based on |X4|.

        .. note::

            This method also updates the shape of log sequence |Q9|.

        |X4| determines the time base of the unit hydrograph.  A value of
        |X4| being not larger than the simulation step size is
        identical with applying no unit hydrograph at all:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(0.6)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (1,)
        >>> derived.uh1
        uh1(1.0)

        Note that, due to difference of the parameter and the simulation
        step size in the given example, the largest assignment resulting
        in a `inactive` unit hydrograph is 1/2:

        >>> x4(1.)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (1,)
        >>> derived.uh1
        uh1(1.0)

        |X4| larger than 1

        >>> x4(1.8)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (2,)
        >>> derived.uh1
        uh1(0.230048, 0.769952)

        >>> x4(6.3)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (7,)
        >>> derived.uh1
        uh1(0.010038, 0.046746, 0.099694, 0.16474, 0.239926, 0.324027, 0.11483)

        Check for sum equal to 1
        >>> import numpy
        >>> numpy.sum(derived.uh1)
        1.0

        """
        x4 = self.subpars.pars.control.x4
        quh1 = self.subpars.pars.model.sequences.logs.quh1
        # Determine UH parameters...
        if x4 <= 1.0:
            # ...when x4 smaller than or equal to the simulation time step.
            self.shape = 1
            quh1.shape = 1
            self(1.0)
        else:
            index = numpy.arange(1, numpy.ceil(x4) + 1)
            sh1j = (index / x4) ** 2.5
            sh1j_1 = ((index - 1) / x4) ** 2.5
            sh1j[index >= x4] = 1
            sh1j_1[index - 1 >= x4] = 1
            self.shape = len(sh1j)
            uh1 = self.values
            quh1.shape = len(uh1)
            uh1[:] = sh1j - sh1j_1

            # sum should be equal to one but better normalize
            self(uh1 / numpy.sum(uh1))


class UH2(parametertools.Parameter):
    """Unit hydrograph UH2 ordinates [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling = False

    CONTROLPARAMETERS = (grxjland_control.X4,)

    def update(self):
        """Update |UH2| based on |X4|.

        .. note::

            This method also updates the shape of log sequence |Q1|.

        2 x |X4| determines the time base of the unit hydrograph. If X4 is smaller or
        equal to 1, UH2 has two ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(0.6)
        >>> derived.uh2.update()
        >>> logs.quh2.shape
        (2,)
        >>> derived.uh2
        uh2(0.967925, 0.032075)

        |X4| larger than 1

        >>> x4(2.8)
        >>> derived.uh2.update()
        >>> logs.quh2.shape
        (6,)
        >>> derived.uh2
        uh2(0.038113, 0.177487, 0.368959, 0.292023, 0.112789, 0.010628)

        Check for sum equal to 1
        >>> import numpy
        >>> numpy.sum(derived.uh2)
        1.0

        |X4| smaller or equal to 0.5
        >>> x4(0.5)
        >>> derived.uh2.update()
        >>> logs.quh2.shape
        (2,)
        >>> derived.uh2
        uh2(1.0, 0.0)

        Check for sum equal to 1
        >>> import numpy
        >>> numpy.sum(derived.uh2)
        1.0

        """
        x4 = self.subpars.pars.control.x4
        quh2 = self.subpars.pars.model.sequences.logs.quh2
        # Determine UH parameters...
        if x4 <= 1.0:
            index = numpy.arange(1, 3)
        else:
            index = numpy.arange(1, numpy.ceil(x4 * 2) + 1)

        nmb_uhs = len(index)
        sh2j = numpy.zeros(shape=nmb_uhs)
        sh2j_1 = numpy.zeros(shape=nmb_uhs)

        for idx in range(nmb_uhs):
            if index[idx] <= x4:
                sh2j[idx] = 0.5 * (index[idx] / x4) ** 2.5
            elif x4 < index[idx] < 2.0 * x4:
                sh2j[idx] = 1.0 - 0.5 * (2.0 - index[idx] / x4) ** 2.5
            else:
                sh2j[idx] = 1

            if index[idx] - 1 <= x4:
                sh2j_1[idx] = 0.5 * ((index[idx] - 1) / x4) ** 2.5
            elif x4 < index[idx] - 1 < 2.0 * x4:
                sh2j_1[idx] = 1.0 - 0.5 * (2.0 - (index[idx] - 1) / x4) ** 2.5
            else:
                sh2j_1[idx] = 1

        self.shape = len(index)
        quh2.shape = len(index)
        uh2 = self.values
        uh2[:] = sh2j - sh2j_1
        self(uh2 / numpy.sum(uh2))


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (grxjland_control.Area,)

    def update(self):
        """Update |QFactor| based on |Area| and the current simulation
        step size.

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> area(50.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(0.578704)

        change simulatio step to 1 h

        >>> simulationstep('1h')
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(13.888889)

        """
        self(
            self.subpars.pars.control.area
            * 1000.0
            / hydpy.pub.options.simulationstep.seconds
        )
