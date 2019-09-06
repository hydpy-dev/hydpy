# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools


class NmbSegments(parametertools.Parameter):
    """Number of river segments [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def update(self):
        """Determines in how many segments the whole reach needs to be
        divided to approximate the desired lag time via integer rounding.
        Adjusts the shape of sequence |QJoints| additionally.

        Required control parameters:
          |Lag|

        Calculated derived parameters:
          |NmbSegments|

        Prepared state sequence:
          |QJoints|

        Examples:

            Define a lag time of 1.4 days and a simulation step size of 12
            hours:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> simulationstep('12h')
            >>> lag(1.4)

            Then the actual lag value for the simulation step size is 2.8

            >>> lag
            lag(1.4)
            >>> lag.value
            2.8

            Through rounding the number of segments is determined:

            >>> derived.nmbsegments.update()
            >>> derived.nmbsegments
            nmbsegments(3)

            The number of joints is always the number of segments plus one:

            >>> states.qjoints.shape
            (4,)
        """
        pars = self.subpars.pars
        self(int(round(pars.control.lag)))
        pars.model.sequences.states.qjoints.shape = self+1


class C1(parametertools.Parameter):
    """First coefficient of the Muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., .5)

    def update(self):
        """Update |C1| based on :math:`c_1 = \\frac{Damp}{1+Damp}`.

        Examples:

            The first examples show the calculated value of |C1| for
            the lowest possible value of |Lag|, the lowest possible value,
            and an intermediate value:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> damp(0.0)
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.0)
            >>> damp(1.0)
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.5)
            >>> damp(0.25)
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.2)

            For to low and to high values of |Lag|, clipping is performed:
            >>> damp.value = -0.1
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.0)
            >>> damp.value = 1.1
            >>> derived.c1.update()
            >>> derived.c1
            c1(0.5)
        """
        damp = self.subpars.pars.control.damp
        self(numpy.clip(damp/(1.+damp), 0., .5))


class C2(parametertools.Parameter):
    """Second coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)

    def update(self):
        """Update |C2| based on :math:`c_2 = 1.-c_1-c_3`.

        Examples:

            The following examples show the calculated value of |C2| are
            clipped when to low or to high:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> derived.c1 = 0.6
            >>> derived.c3 = 0.1
            >>> derived.c2.update()
            >>> derived.c2
            c2(0.3)
            >>> derived.c1 = 1.6
            >>> derived.c2.update()
            >>> derived.c2
            c2(0.0)
            >>> derived.c1 = -1.6
            >>> derived.c2.update()
            >>> derived.c2
            c2(1.0)
        """
        der = self.subpars
        self(numpy.clip(1. - der.c1 - der.c3, 0., 1.))


class C3(parametertools.Parameter):
    """Third coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., .5)

    def update(self):
        """Update |C3| based on :math:`c_1 = c_3`.

        Example:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> derived.c1 = 0.5
            >>> derived.c3.update()
            >>> derived.c3
            c3(0.5)
        """
        self(self.subpars.c1)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of hstream, indirectly defined by the user."""
    CLASSES = (NmbSegments,
               C1,
               C3,
               C2)
