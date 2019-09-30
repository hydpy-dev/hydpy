# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.hstream import hstream_derived
from hydpy.models.hstream import hstream_states
from hydpy.models.hstream import hstream_inlets
from hydpy.models.hstream import hstream_outlets


class Calc_QJoints_V1(modeltools.Method):
    """Apply the routing equation.

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
    DERIVEDPARAMETERS = (
        hstream_derived.NmbSegments,
        hstream_derived.C1,
        hstream_derived.C2,
        hstream_derived.C3,
    )
    UPDATEDSEQUENCES = (
        hstream_states.QJoints,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        new = model.sequences.states.fastaccess_new
        old = model.sequences.states.fastaccess_old
        for j in range(der.nmbsegments):
            new.qjoints[j+1] = (der.c1*new.qjoints[j] +
                                der.c2*old.qjoints[j] +
                                der.c3*old.qjoints[j+1])


class Pick_Q_V1(modeltools.Method):
    """Assign the actual value of the inlet sequence to the upper joint
    of the subreach upstream."""
    REQUIREDSEQUENCES = (
        hstream_inlets.Q,
    )
    RESULTSEQUENCES = (
        hstream_states.QJoints,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inl = model.sequences.inlets.fastaccess
        new = model.sequences.states.fastaccess_new
        new.qjoints[0] = 0.
        for idx in range(inl.len_q):
            new.qjoints[0] += inl.q[idx][0]


class Pass_Q_V1(modeltools.Method):
    """Assing the actual value of the lower joint of of the subreach
    downstream to the outlet sequence."""
    REQUIREDSEQUENCES = (
        hstream_states.QJoints,
    )
    RESULTSEQUENCES = (
        hstream_outlets.Q,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        new = model.sequences.states.fastaccess_new
        out = model.sequences.outlets.fastaccess
        out.q[0] += new.qjoints[der.nmbsegments]


class Model(modeltools.AdHocModel):
    """The HydPy-H-Stream model."""
    INLET_METHODS = (
        Pick_Q_V1,
    )
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_QJoints_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (
        Pass_Q_V1,
    )
    SENDER_METHODS = ()
