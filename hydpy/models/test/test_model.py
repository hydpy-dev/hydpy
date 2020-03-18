# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.test import test_control
from hydpy.models.test import test_solver
from hydpy.models.test import test_fluxes
from hydpy.models.test import test_states


class Calc_Q_V1(modeltools.Method):
    """Calculate the actual storage loss.

    This simple equation is continuous but potentially stiff.

    Basic equation:
      :math:`Q = K \\cdot S`

    Example:

       >>> from hydpy.models.test import *
       >>> parameterstep()
       >>> k(0.5)
       >>> states.s = 2.0
       >>> model.calc_q_v1()
       >>> fluxes.q
       q(1.0)
    """
    CONTROLPARAMETERS = (
        test_control.K,
    )
    REQUIREDSEQUENCES = (
        test_states.S,
    )
    RESULTSEQUENCES = (
        test_fluxes.Q,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.q = con.k*sta.s


class Calc_Q_V2(modeltools.Method):
    """Calculate the actual storage loss.

    This simple equation is discontinuous.

    Basic equation:
      :math:`Q = \\Bigl \\lbrace
      {
      {K \\ | \\ S > 0}
      \\atop
      {0 \\ | \\ S \\leq 0}
      }`

    Examples:

       >>> from hydpy.models.test import *
       >>> parameterstep()
       >>> k(0.5)
       >>> states.s = 2.0
       >>> model.calc_q_v2()
       >>> fluxes.q
       q(0.5)
       >>> states.s = -1.0
       >>> model.calc_q_v2()
       >>> fluxes.q
       q(0.0)
    """
    CONTROLPARAMETERS = (
        test_control.K,
    )
    REQUIREDSEQUENCES = (
        test_states.S,
    )
    RESULTSEQUENCES = (
        test_fluxes.Q,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.s > 0.:
            flu.q = con.k
        else:
            flu.q = 0.


class Calc_QV_V1(modeltools.Method):
    """Calculate the actual storage losses.

    Identical with |Calc_Q_V1|, but working on a vector of states.

    Basic equation:
      :math:`Q = K \\cdot S`

    Example:

       >>> from hydpy.models.test import *
       >>> parameterstep()
       >>> n(2)
       >>> k(0.5)
       >>> states.sv = 2.0, 3.0
       >>> model.calc_qv_v1()
       >>> fluxes.qv
       qv(1.0, 1.5)
    """
    CONTROLPARAMETERS = (
        test_control.N,
        test_control.K,
    )
    REQUIREDSEQUENCES = (
        test_states.SV,
    )
    RESULTSEQUENCES = (
        test_fluxes.QV,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for i in range(con.n):
            flu.qv[i] = con.k*sta.sv[i]


class Calc_S_V1(modeltools.Method):
    """Calculate the actual storage content.

    Basic equation:
      :math:`\\frac{dS}{dt} = Q`

    Example:

       >>> from hydpy.models.test import *
       >>> parameterstep()
       >>> states.s.old = 1.0
       >>> fluxes.q = 0.8
       >>> model.calc_s_v1()
       >>> states.s
       s(0.2)
    """
    CONTROLPARAMETERS = (
        test_control.K,
    )
    REQUIREDSEQUENCES = (
        test_fluxes.Q,
    )
    UPDATEDSEQUENCES = (
        test_states.S,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.s = old.s-flu.q


class Calc_SV_V1(modeltools.Method):
    """Calculate the actual storage contenst.

    Identical with |Calc_S_V1|, but working on a vector of fluxes.

    Basic equation:
      :math:`\\frac{dS}{dt} = Q`

    Example:

       >>> from hydpy.models.test import *
       >>> parameterstep()
       >>> n(2)
       >>> states.sv.old = 1.0, 2.0
       >>> fluxes.qv = 0.8
       >>> model.calc_sv_v1()
       >>> states.sv
       sv(0.2, 1.2)
    """
    CONTROLPARAMETERS = (
        test_control.N,
        test_control.K,
    )
    REQUIREDSEQUENCES = (
        test_fluxes.QV,
    )
    UPDATEDSEQUENCES = (
        test_states.SV,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for i in range(con.n):
            new.sv[i] = old.sv[i]-flu.qv[i]


class Model(modeltools.ELSModel):
    """Test model."""
    SOLVERPARAMETERS = (
        test_solver.AbsErrorMax,
        test_solver.RelErrorMax,
        test_solver.RelDTMin,
        test_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        Calc_Q_V1,
        Calc_Q_V2,
        Calc_QV_V1,
    )
    FULL_ODE_METHODS = (
        Calc_S_V1,
        Calc_SV_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
