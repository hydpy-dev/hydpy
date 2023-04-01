# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
# ...from site-packages
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.dummy import dummy_inputs
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


class Get_InterceptedWater_V1(modeltools.Method):
    """Get the current precipitation from the selected zone.

    Example:

        >>> from hydpy.models.dummy import *
        >>> parameterstep()
        >>> inputs.interceptedwater.shape = 2
        >>> inputs.interceptedwater = 2.0, 4.0
        >>> model.get_interceptedwater_v1(0)
        2.0
        >>> model.get_interceptedwater_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (dummy_inputs.InterceptedWater,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.interceptedwater[k]


class Get_SoilWater_V1(modeltools.Method):
    """Get the current precipitation from the selected zone.

    Example:

        >>> from hydpy.models.dummy import *
        >>> parameterstep()
        >>> inputs.soilwater.shape = 2
        >>> inputs.soilwater = 2.0, 4.0
        >>> model.get_soilwater_v1(0)
        2.0
        >>> model.get_soilwater_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (dummy_inputs.SoilWater,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.soilwater[k]


class Get_SnowCover_V1(modeltools.Method):
    """Get the current precipitation from the selected zone.

    Example:

        >>> from hydpy.models.dummy import *
        >>> parameterstep()
        >>> inputs.snowcover.shape = 2
        >>> inputs.snowcover = 2.0, 4.0
        >>> model.get_snowcover_v1(0)
        2.0
        >>> model.get_snowcover_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (dummy_inputs.SnowCover,)

    @staticmethod
    def __call__(model: modeltools.Model, k: int) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.snowcover[k]


class Model(modeltools.AdHocModel):
    """The HydPy-Dummy model."""

    INLET_METHODS = (Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        Get_InterceptedWater_V1,
        Get_SoilWater_V1,
        Get_SnowCover_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
