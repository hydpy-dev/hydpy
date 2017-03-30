# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import sys
import warnings
# ...third party
import numpy
# ...HydPy specific
from hydpy.core import objecttools
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

###############################################################################
# Model
###############################################################################

class Model(modeltools.Model):
    """The HydPy-H-Stream model."""

    def run(self, idx):
        """Apply the routing equation.

        Required derived parameters:
          :class:`NmbSegments`
          :class:`C1`
          :class:`C2`
          :class:`C3`

        Updated state sequence:
          :class:`QJoints`

        Basic equation:
          :math:`Q_{space+1,time+1} =
          c1 \\cdot Q_{space,time+1} +
          c2 \\cdot Q_{space,time} +
          c3 \\cdot Q_{space+1,time}`

        Examples:

            Firstly, define a reach divided into 4 segments:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> derived.nmbsegments(4)
            >>> states.qjoints.shape = 5

            Zero damping is achieved through the following coefficients:

            >>> derived.c1(0.)
            >>> derived.c2(1.)
            >>> derived.c3(0.)

            For initialization, assume a base flow of 2m³/s:

            >>> states.qjoints.old = 2.
            >>> states.qjoints.new = 2.

            Through successive assignements of different discharge values
            to the upper junction one can see, that these discharge values
            are simply shifted from each junction to the respective lower
            junction at each time step:

            >>> states.qjoints[0] = 5.
            >>> model.run(0)
            >>> model.new2old()
            >>> states.qjoints
            qjoints(5.0, 2.0, 2.0, 2.0, 2.0)
            >>> states.qjoints[0] = 8.
            >>> model.run(1)
            >>> model.new2old()
            >>> states.qjoints
            qjoints(8.0, 5.0, 2.0, 2.0, 2.0)
            >>> states.qjoints[0] = 6.
            >>> model.run(1)
            >>> model.new2old()
            >>> states.qjoints
            qjoints(6.0, 8.0, 5.0, 2.0, 2.0)

            With the maximum damping allowed, the values of the derived
            parameters are:

            >>> derived.c1(.5)
            >>> derived.c2(.0)
            >>> derived.c3(.5)

            Assuming again a base flow of 2m³/s and the same input values
            results in:

            >>> states.qjoints.old = 2.
            >>> states.qjoints.new = 2.

            >>> states.qjoints[0] = 5.
            >>> model.run(0)
            >>> model.new2old()
            >>> states.qjoints
            qjoints(5.0, 3.5, 2.75, 2.375, 2.1875)
            >>> states.qjoints[0] = 8.
            >>> model.run(1)
            >>> model.new2old()
            >>> states.qjoints
            qjoints(8.0, 5.75, 4.25, 3.3125, 2.75)
            >>> states.qjoints[0] = 6.
            >>> model.run(1)
            >>> model.new2old()
            >>> states.qjoints
            qjoints(6.0, 5.875, 5.0625, 4.1875, 3.46875)

        """
        der = self.parameters.derived.fastaccess
        new = self.sequences.states.fastaccess_new
        old = self.sequences.states.fastaccess_old
        for j in range(der.nmbsegments):
            new.qjoints[j+1] = (der.c1*new.qjoints[j] +
                                der.c2*old.qjoints[j] +
                                der.c3*old.qjoints[j+1])

    def updateinlets(self, idx):
        """Assign the actual value of the inlet sequence to the upper joint
        of the subreach upstream."""
        sta = self.sequences.states.fastaccess
        inl = self.sequences.inlets.fastaccess
        sta.qjoints[0] = inl.q[0]

    def updateoutlets(self, idx):
        """Assing the actual value of the lower joint of of the subreach
        downstream to the outlet sequence."""
        der = self.parameters.derived.fastaccess
        sta = self.sequences.states.fastaccess
        out = self.sequences.outlets.fastaccess
        out.q[0] += sta.qjoints[der.nmbsegments]

###############################################################################
# Parameter definitions
###############################################################################

class Lag(parametertools.SingleParameter):
    """Time lag between inflow and outflow [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)

class Damp(parametertools.SingleParameter):
    """Damping of the hydrograph [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)

class ControlParameters(parametertools.SubParameters):
    """Control parameters of hstream, directly defined by the user."""
    _PARCLASSES = (Lag, Damp)

# Derived Parameters ##########################################################

class NmbSegments(parametertools.SingleParameter):
    """Number of river segments [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

class C1(parametertools.SingleParameter):
    """First coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., .5)

class C2(parametertools.SingleParameter):
    """Second coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)

class C3(parametertools.SingleParameter):
    """Third coefficient of the muskingum working formula [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., .5)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of hstream, indirectly defined by the user."""
    _PARCLASSES = (NmbSegments, C1, C2, C3)

# Parameter container #########################################################

class Parameters(parametertools.Parameters):
    """All parameters of the hstream model."""

    def update(self):
        """Determines the values of the parameters handled by
        :class:`DerivedParameters` based on the values of the parameters.
        """
        self.calc_nmbsegments()
        self.calc_coefficients()

    def calc_nmbsegments(self):
        """Determines in how many segments the whole reach needs to be
        divided to approximate the desired lag time via integer rounding.
        Adjusts the shape of sequence :class:`QJoints` additionally.

        Required control parameters:
          :class:`Lag`

        Calculated derived parameters:
          :class:`NmbSegments`

        Prepared state sequence:
          :class:`QJoints`

        Example:

            Define a lag time of 1.4 days and a simulation step size of 12
            hours:

            >>> from hydpy.models.hstream import *
            >>> parameterstep('1d')
            >>> simulationstep('12h', warn=False)
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
          :class:`Damp`

        Calculated derived parameters:
          :class:`C1`
          :class:`C2`
          :class:`C3`

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

###############################################################################
# Sequence Definitions
###############################################################################

# State Sequences #############################################################

class QJoints(sequencetools.StateSequence):
    """Runoff at the segment junctions [m³/s]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

    def __call__(self, *args):
        try:
            sequencetools.StateSequence.__call__(self, *args)
        except BaseException:
            message = sys.exc_info()[1]
            sequencetools.StateSequence.__call__(self, numpy.mean(args))
            warnings.warn('Note that, due to the following problem, the'
                          'affected HydPy-H-Stream model could be initialised '
                          'with an averaged value only: %s' % message)

class StateSequences(sequencetools.StateSequences):
    """State sequences of the hstream model."""
    _SEQCLASSES = (QJoints,)

# Link Sequences ##############################################################

class Q(sequencetools.LinkSequence):
    """Runoff [m³/s]."""
    NDIM, NUMERIC = 0, False

class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the hstream model."""
    _SEQCLASSES = (Q,)

class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of the hstream model."""
    _SEQCLASSES = (Q,)

# Sequence container ##########################################################

class Sequences(sequencetools.Sequences):
    """All sequences of the hstream model."""


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
