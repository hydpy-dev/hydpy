# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools


def calc_qjoints_v1(self):
    """Apply the routing equation.

    Required derived parameters:
      |NmbSegments|
      |C1|
      |C2|
      |C3|

    Updated state sequence:
      |QJoints|

    Basic equation:
      :math:`Q_{space+1,time+1} =
      c1 \\cdot Q_{space,time+1} +
      c2 \\cdot Q_{space,time} +
      c3 \\cdot Q_{space+1,time}`

    Examples:

        Firstly, define a reach divided into four segments:

        >>> from hydpy.models.hstream import *
        >>> parameterstep('1d')
        >>> derived.nmbsegments(4)
        >>> states.qjoints.shape = 5

        Zero damping is achieved through the following coefficients:

        >>> derived.c1(0.0)
        >>> derived.c2(1.0)
        >>> derived.c3(0.0)

        For initialization, assume a base flow of 2m³/s:

        >>> states.qjoints.old = 2.0
        >>> states.qjoints.new = 2.0

        Through successive assignements of different discharge values
        to the upper junction one can see that these discharge values
        are simply shifted from each junction to the respective lower
        junction at each time step:

        >>> states.qjoints[0] = 5.0
        >>> model.calc_qjoints_v1()
        >>> model.new2old()
        >>> states.qjoints
        qjoints(5.0, 2.0, 2.0, 2.0, 2.0)
        >>> states.qjoints[0] = 8.0
        >>> model.calc_qjoints_v1()
        >>> model.new2old()
        >>> states.qjoints
        qjoints(8.0, 5.0, 2.0, 2.0, 2.0)
        >>> states.qjoints[0] = 6.0
        >>> model.calc_qjoints_v1()
        >>> model.new2old()
        >>> states.qjoints
        qjoints(6.0, 8.0, 5.0, 2.0, 2.0)

        With the maximum damping allowed, the values of the derived
        parameters are:

        >>> derived.c1(0.5)
        >>> derived.c2(0.0)
        >>> derived.c3(0.5)

        Assuming again a base flow of 2m³/s and the same input values
        results in:

        >>> states.qjoints.old = 2.0
        >>> states.qjoints.new = 2.0

        >>> states.qjoints[0] = 5.0
        >>> model.calc_qjoints_v1()
        >>> model.new2old()
        >>> states.qjoints
        qjoints(5.0, 3.5, 2.75, 2.375, 2.1875)
        >>> states.qjoints[0] = 8.0
        >>> model.calc_qjoints_v1()
        >>> model.new2old()
        >>> states.qjoints
        qjoints(8.0, 5.75, 4.25, 3.3125, 2.75)
        >>> states.qjoints[0] = 6.0
        >>> model.calc_qjoints_v1()
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


def pick_q_v1(self):
    """Assign the actual value of the inlet sequence to the upper joint
    of the subreach upstream."""
    inl = self.sequences.inlets.fastaccess
    new = self.sequences.states.fastaccess_new
    new.qjoints[0] = 0.
    for idx in range(inl.len_q):
        new.qjoints[0] += inl.q[idx][0]


def pass_q_v1(self):
    """Assing the actual value of the lower joint of of the subreach
    downstream to the outlet sequence."""
    der = self.parameters.derived.fastaccess
    new = self.sequences.states.fastaccess_new
    out = self.sequences.outlets.fastaccess
    out.q[0] += new.qjoints[der.nmbsegments]


class Model(modeltools.Model):
    """The HydPy-H-Stream model."""
    INLET_METHODS = (pick_q_v1,)
    RUN_METHODS = (calc_qjoints_v1,)
    OUTLET_METHODS = (pass_q_v1,)
