# -*- coding: utf-8 -*-

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools


class Parameters(parametertools.Parameters):
    """All parameters of the hstream model."""

    def update(self):
        """Determines the values of the parameters handled by
        |DerivedParameters| based on the values of the parameters.
        """
        self.calc_nmbsegments()
        self.calc_coefficients()

    def calc_nmbsegments(self):
        """Determines in how many segments the whole reach needs to be
        divided to approximate the desired lag time via integer rounding.
        Adjusts the shape of sequence |QJoints| additionally.

        Required control parameters:
          |Lag|

        Calculated derived parameters:
          |NmbSegments|

        Prepared state sequence:
          |QJoints|

        Example:

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

            >>> model.parameters.calc_nmbsegments()
            >>> derived.nmbsegments
            nmbsegments(3)

            The number of joints is always the number of segments plus one:

            >>> states.qjoints.shape
            (4,)

        """
        con = self.control
        der = self.derived
        der.nmbsegments = int(round(con.lag))
        self.model.sequences.states.qjoints.shape = der.nmbsegments+1

    def calc_coefficients(self):
        """Calculates the Muskingum coefficients.

        Required control parameters:
          |Damp|

        Calculated derived parameters:
          |C1|
          |C2|
          |C3|

        Basic equations:
          :math:`c_1 = \\frac{Damp}{1+Damp}`\n
          :math:`c_3 = \\frac{Damp}{1+Damp}`\n
          :math:`c_2 = 1.-c_1-c_3`

        Examples:

            If no damping is required, the coeffients are:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> damp(0.)
            >>> model.parameters.calc_coefficients()
            >>> derived.c1, derived.c2, derived.c3
            (c1(0.0), c2(1.0), c3(0.0))

            The strongest damping is achieved through:

            >>> damp(1.)
            >>> model.parameters.calc_coefficients()
            >>> derived.c1, derived.c2, derived.c3
            (c1(0.5), c2(0.0), c3(0.5))

            And finally an intermediate example:

            >>> damp(.25)
            >>> model.parameters.calc_coefficients()
            >>> derived.c1, derived.c2, derived.c3
            (c1(0.2), c2(0.6), c3(0.2))

        """
        con = self.control
        der = self.derived
        der.c1 = der.c3 = numpy.clip(con.damp/(1.+con.damp), 0., .5)
        der.c2 = numpy.clip(1.-der.c1-der.c3, 0., 1.)
