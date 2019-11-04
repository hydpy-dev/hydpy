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


class Model(modeltools.ELSModel):
    """Test model."""
    SOLVERPARAMETERS = (
        test_solver.AbsErrorMax,
        test_solver.RelDTMin,
    )
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    PART_ODE_METHODS = (
        Calc_Q_V1,
        Calc_Q_V2,
    )
    FULL_ODE_METHODS = (
        Calc_S_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
