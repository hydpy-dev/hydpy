# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.musk import musk_control
from hydpy.models.musk import musk_states
from hydpy.models.musk import musk_inlets
from hydpy.models.musk import musk_outlets


class Pick_Q_V1(modeltools.Method):
    """Assign the actual value of the inlet sequence to the upper endpoint of the first
    channel segment."""

    REQUIREDSEQUENCES = (musk_inlets.Q,)
    RESULTSEQUENCES = (musk_states.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inl = model.sequences.inlets.fastaccess
        new = model.sequences.states.fastaccess_new
        new.q[0] = 0.0
        for idx in range(inl.len_q):
            new.q[0] += inl.q[idx][0]


class Calc_Q_V1(modeltools.Method):
    r"""Apply the routing equation with fixed coefficients.

    Basic equation:
      :math:`Q_{space+1,time+1} =
      Coefficients_0 \cdot Q_{space,time+1} +
      Coefficients_1 \cdot Q_{space,time} +
      Coefficients_2 \cdot Q_{space+1,time}`

    Examples:

        First, define a channel divided into four segments:

        >>> from hydpy.models.musk import *
        >>> parameterstep("1d")
        >>> nmbsegments(4)

        The following coefficients correspond to pure translation without diffusion:

        >>> coefficients(0.0, 1.0, 0.0)

        The initial flow is 2 m³/s:

        >>> states.q.old = 2.0
        >>> states.q.new = 2.0

        Successive invocations of method |Calc_Q_V1| shift the given inflows to the
        next lower endpoints at each time step:

        >>> states.q[0] = 5.0
        >>> model.calc_q_v1()
        >>> model.new2old()
        >>> states.q
        q(5.0, 2.0, 2.0, 2.0, 2.0)

        >>> states.q[0] = 8.0
        >>> model.calc_q_v1()
        >>> model.new2old()
        >>> states.q
        q(8.0, 5.0, 2.0, 2.0, 2.0)

        >>> states.q[0] = 6.0
        >>> model.calc_q_v1()
        >>> model.new2old()
        >>> states.q
        q(6.0, 8.0, 5.0, 2.0, 2.0)

        We repeat the example with strong wave diffusion:

        >>> coefficients(0.5, 0.0, 0.5)

        >>> states.q.old = 2.0
        >>> states.q.new = 2.0

        >>> states.q[0] = 5.0
        >>> model.calc_q_v1()
        >>> model.new2old()
        >>> states.q
        q(5.0, 3.5, 2.75, 2.375, 2.1875)

        >>> states.q[0] = 8.0
        >>> model.calc_q_v1()
        >>> model.new2old()
        >>> states.q
        q(8.0, 5.75, 4.25, 3.3125, 2.75)

        >>> states.q[0] = 6.0
        >>> model.calc_q_v1()
        >>> model.new2old()
        >>> states.q
        q(6.0, 5.875, 5.0625, 4.1875, 3.46875)
    """
    CONTROLPARAMETERS = (
        musk_control.NmbSegments,
        musk_control.Coefficients,
    )
    UPDATEDSEQUENCES = (musk_states.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        old = model.sequences.states.fastaccess_old
        for j in range(con.nmbsegments):
            new.q[j + 1] = (
                con.coefficients[0] * new.q[j]
                + con.coefficients[1] * old.q[j]
                + con.coefficients[2] * old.q[j + 1]
            )


class Pass_Q_V1(modeltools.Method):
    """Pass the actual value of the lower endpoint of the last channel segment to the
    outlet sequence."""

    CONTROLPARAMETERS = (musk_control.NmbSegments,)
    REQUIREDSEQUENCES = (musk_states.Q,)
    RESULTSEQUENCES = (musk_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        out = model.sequences.outlets.fastaccess
        out.q[0] += new.q[con.nmbsegments]


class Model(modeltools.AdHocModel):
    """The HydPy-Musk model."""

    INLET_METHODS = (Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (Calc_Q_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()
