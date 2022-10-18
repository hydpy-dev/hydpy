# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.exch import exch_control
from hydpy.models.exch import exch_factors
from hydpy.models.exch import exch_fluxes
from hydpy.models.exch import exch_logs
from hydpy.models.exch import exch_receivers
from hydpy.models.exch import exch_outlets


class Pic_LoggedWaterLevel_V1(modeltools.Method):
    r"""Pic the logged water level from a receiver node.

    Basic equation:
      :math:`LoggedWaterLevel = L`
    """

    REQUIREDSEQUENCES = (exch_receivers.L,)
    RESULTSEQUENCES = (exch_logs.LoggedWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        for idx in range(2):
            log.loggedwaterlevel[idx] = rec.l[idx][0]


class Update_WaterLevel_V1(modeltools.Method):
    r"""Update the factor sequence |WaterLevel|.

    Basic equation:
      :math:`WaterLevel = LoggedWaterLevel`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> logs.loggedwaterlevel = 2.0, 4.0
        >>> model.update_waterlevel_v1()
        >>> factors.waterlevel
        waterlevel(2.0, 4.0)
    """

    REQUIREDSEQUENCES = (exch_logs.LoggedWaterLevel,)
    RESULTSEQUENCES = (exch_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(2):
            fac.waterlevel[idx] = log.loggedwaterlevel[idx]


class Calc_DeltaWaterLevel_V1(modeltools.Method):
    r"""Calculate the effective difference of both water levels.

    Basic equation:
      :math:`DeltaWaterLevel =
      max(WaterLevel_0, CrestHeight) - max(WaterLevel_1, CrestHeight)`

    Examples:

        "Effective difference" means that only the height above the crest counts.
        The first example illustrates this for fixed water levels and a variable
        crest height:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model=model,
        ...                 method=model.calc_deltawaterlevel_v1,
        ...                 last_example=5,
        ...                 parseqs=(control.crestheight, factors.deltawaterlevel))
        >>> test.nexts.crestheight = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> factors.waterlevel = 4.0, 2.0
        >>> test()
        | ex. | crestheight | deltawaterlevel |
        ---------------------------------------
        |   1 |         1.0 |             2.0 |
        |   2 |         2.0 |             2.0 |
        |   3 |         3.0 |             1.0 |
        |   4 |         4.0 |             0.0 |
        |   5 |         5.0 |             0.0 |

        Method |Calc_DeltaWaterLevel_V1| modifies the basic equation given above to
        also work for an inverse gradient:

        >>> factors.waterlevel = 2.0, 4.0
        >>> test()
        | ex. | crestheight | deltawaterlevel |
        ---------------------------------------
        |   1 |         1.0 |            -2.0 |
        |   2 |         2.0 |            -2.0 |
        |   3 |         3.0 |            -1.0 |
        |   4 |         4.0 |             0.0 |
        |   5 |         5.0 |             0.0 |
    """
    CONTROLPARAMETERS = (exch_control.CrestHeight,)
    REQUIREDSEQUENCES = (exch_factors.WaterLevel,)
    RESULTSEQUENCES = (exch_factors.DeltaWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        d_wl0 = max(fac.waterlevel[0], con.crestheight)
        d_wl1 = max(fac.waterlevel[1], con.crestheight)
        fac.deltawaterlevel = d_wl0 - d_wl1


class Calc_PotentialExchange_V1(modeltools.Method):
    r"""Calculate the potential exchange that strictly follows the weir formula without
    taking any other limitations into account.

    Basic equation:
      :math:`PotentialExchange =
      FlowCoefficient \cdot CrestWidth \cdot DeltaWaterLevel ^ {FlowExponent}`

    Examples:

        Method |Calc_PotentialExchange_V1| modifies the given basic equation to work
        for positive and negative gradients:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> crestwidth(3.0)
        >>> flowcoefficient(0.5)
        >>> flowexponent(2.0)
        >>> factors.deltawaterlevel = 2.0
        >>> model.calc_potentialexchange_v1()
        >>> fluxes.potentialexchange
        potentialexchange(6.0)

        >>> factors.deltawaterlevel = -2.0
        >>> model.calc_potentialexchange_v1()
        >>> fluxes.potentialexchange
        potentialexchange(-6.0)
    """
    CONTROLPARAMETERS = (
        exch_control.CrestWidth,
        exch_control.FlowCoefficient,
        exch_control.FlowExponent,
    )
    REQUIREDSEQUENCES = (exch_factors.DeltaWaterLevel,)
    RESULTSEQUENCES = (exch_fluxes.PotentialExchange,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if fac.deltawaterlevel >= 0.0:
            d_dwl = fac.deltawaterlevel
            d_sig = 1.0
        else:
            d_dwl = -fac.deltawaterlevel
            d_sig = -1.0
        flu.potentialexchange = d_sig * (
            con.flowcoefficient * con.crestwidth * d_dwl**con.flowexponent
        )


class Calc_ActualExchange_V1(modeltools.Method):
    r"""Calculate the actual exchange.

    Basic equation:
      :math:`ActualExchange = min(PotentialExchange, AllowedExchange)`

    Examples:

        Method |Calc_ActualExchange_V1| modifies the given basic equation to work
        for positive and negative gradients:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> allowedexchange(2.0)
        >>> fluxes.potentialexchange = 1.0
        >>> model.calc_actualexchange_v1()
        >>> fluxes.actualexchange
        actualexchange(1.0)

        >>> fluxes.potentialexchange = 3.0
        >>> model.calc_actualexchange_v1()
        >>> fluxes.actualexchange
        actualexchange(2.0)

        >>> fluxes.potentialexchange = -1.0
        >>> model.calc_actualexchange_v1()
        >>> fluxes.actualexchange
        actualexchange(-1.0)

        >>> fluxes.potentialexchange = -3.0
        >>> model.calc_actualexchange_v1()
        >>> fluxes.actualexchange
        actualexchange(-2.0)
    """
    CONTROLPARAMETERS = (exch_control.AllowedExchange,)
    REQUIREDSEQUENCES = (exch_fluxes.PotentialExchange,)
    RESULTSEQUENCES = (exch_fluxes.ActualExchange,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if flu.potentialexchange >= 0.0:
            flu.actualexchange = min(flu.potentialexchange, con.allowedexchange)
        else:
            flu.actualexchange = max(flu.potentialexchange, -con.allowedexchange)


class Pass_ActualExchange_V1(modeltools.Method):
    """Pass the actual exchange to an outlet node.

    Basic equation:
      :math:`E = ActualExchange`
    """

    REQUIREDSEQUENCES = (exch_fluxes.ActualExchange,)
    RESULTSEQUENCES = (exch_outlets.E,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.e[0][0] -= flu.actualexchange
        out.e[1][0] += flu.actualexchange


class Model(modeltools.AdHocModel):
    """HydPy-Exch base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = (Pic_LoggedWaterLevel_V1,)
    RUN_METHODS = (
        Update_WaterLevel_V1,
        Calc_DeltaWaterLevel_V1,
        Calc_PotentialExchange_V1,
        Calc_ActualExchange_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_ActualExchange_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
