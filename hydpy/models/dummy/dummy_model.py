# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
# ...from site-packages
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.dummy import dummy_inlets
from hydpy.models.dummy import dummy_outlets
from hydpy.models.dummy import dummy_fluxes


class Pick_Q_V1(modeltools.Method):
    """Query the current inflow from all inlet nodes.

    Basic equation:
      :math:`Q_{fluxes} = \\sum Q_{inputs}`
    """

    REQUIREDSEQUENCES = (dummy_inlets.Q,)
    RESULTSEQUENCES = (dummy_fluxes.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.q = 0.0
        for idx in range(inl.len_q):
            flu.q += inl.q[idx][0]


class Pass_Q_V1(modeltools.Method):
    """Uptdate the outlet link sequence.

    Basic equation:
        :math:`Q_{outlets} = Q_{fluxes}`
    """

    REQUIREDSEQUENCES = (dummy_fluxes.Q,)
    RESULTSEQUENCES = (dummy_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.q


class Model(modeltools.AdHocModel):
    """The HydPy-Dummy model."""

    INLET_METHODS = (Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
