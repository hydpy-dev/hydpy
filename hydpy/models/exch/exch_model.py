# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.exch import exch_control
from hydpy.models.exch import exch_derived
from hydpy.models.exch import exch_inlets
from hydpy.models.exch import exch_observers
from hydpy.models.exch import exch_factors
from hydpy.models.exch import exch_fluxes
from hydpy.models.exch import exch_logs
from hydpy.models.exch import exch_receivers
from hydpy.models.exch import exch_outlets
from hydpy.models.exch import exch_senders


class Pick_LoggedWaterLevel_V1(modeltools.Method):
    """Pick the logged water level from a single receiver node.

    Basic equation:
      :math:`LoggedWaterLevel = WaterLevel`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> receivers.waterlevel = 2.0
        >>> model.pick_loggedwaterlevel_v1()
        >>> logs.loggedwaterlevel
        loggedwaterlevel(2.0)

    """

    REQUIREDSEQUENCES = (exch_receivers.WaterLevel,)
    RESULTSEQUENCES = (exch_logs.LoggedWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedwaterlevel[0] = rec.waterlevel


class Pick_LoggedWaterLevels_V1(modeltools.Method):
    """Pic the logged water levels from two receiver nodes.

    Basic equation:
      :math:`LoggedWaterLevels = WaterLevels`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> receivers.waterlevels.shape = 2
        >>> receivers.waterlevels = 2.0, 4.0
        >>> model.pick_loggedwaterlevels_v1()
        >>> logs.loggedwaterlevels
        loggedwaterlevels(2.0, 4.0)
    """

    REQUIREDSEQUENCES = (exch_receivers.WaterLevels,)
    RESULTSEQUENCES = (exch_logs.LoggedWaterLevels,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        for idx in range(2):
            log.loggedwaterlevels[idx] = rec.waterlevels[idx]


class Pick_X_V1(modeltools.Method):
    r"""Pick the input data from multiple input nodes and sum it up.

    Basic equation:
      :math:`X_{factors} = \sum X_{observers}`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> observernodes("n1", "n2")
        >>> observers.x = 1.0, 2.0
        >>> model.pick_x_v1()
        >>> factors.x
        x(3.0)
    """

    CONTROLPARAMETERS = (exch_control.ObserverNodes,)
    REQUIREDSEQUENCES = (exch_observers.X,)
    RESULTSEQUENCES = (exch_factors.X,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        obs = model.sequences.observers.fastaccess
        fac = model.sequences.factors.fastaccess

        fac.x = 0.0
        for i in range(con.observernodes):
            fac.x += obs.x[i]


class Update_WaterLevels_V1(modeltools.Method):
    r"""Update the factor sequence |exch_factors.WaterLevels|.

    Basic equation:
      :math:`WaterLevels = LoggedWaterLevel`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> logs.loggedwaterlevels = 2.0, 4.0
        >>> model.update_waterlevels_v1()
        >>> factors.waterlevels
        waterlevels(2.0, 4.0)
    """

    REQUIREDSEQUENCES = (exch_logs.LoggedWaterLevels,)
    RESULTSEQUENCES = (exch_factors.WaterLevels,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(2):
            fac.waterlevels[idx] = log.loggedwaterlevels[idx]


class Calc_DeltaWaterLevel_V1(modeltools.Method):
    r"""Calculate the effective difference of both water levels.

    Basic equation:
      :math:`DeltaWaterLevel =
      max(WaterLevel_0, CrestHeight) - max(WaterLevel_1, CrestHeight)`

    Examples:

        "Effective difference" means that only the height above the crest counts.  The
        first example illustrates this for fixed water levels and a variable crest
        height:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model=model,
        ...                 method=model.calc_deltawaterlevel_v1,
        ...                 last_example=5,
        ...                 parseqs=(control.crestheight, factors.deltawaterlevel))
        >>> test.nexts.crestheight = 1.0, 2.0, 3.0, 4.0, 5.0
        >>> factors.waterlevels = 4.0, 2.0
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

        >>> factors.waterlevels = 2.0, 4.0
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
    REQUIREDSEQUENCES = (exch_factors.WaterLevels,)
    RESULTSEQUENCES = (exch_factors.DeltaWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        d_wl0 = max(fac.waterlevels[0], con.crestheight)
        d_wl1 = max(fac.waterlevels[1], con.crestheight)
        fac.deltawaterlevel = d_wl0 - d_wl1


class Calc_PotentialExchange_V1(modeltools.Method):
    r"""Calculate the potential exchange that strictly follows the weir formula without
    taking any other limitations into account.

    Basic equation:
      :math:`PotentialExchange =
      FlowCoefficient \cdot CrestWidth \cdot DeltaWaterLevel ^ {FlowExponent}`

    Examples:

        Method |Calc_PotentialExchange_V1| modifies the above basic equation to work
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
      :math:`Exchange = ActualExchange`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> fluxes.actualexchange = 2.0
        >>> outlets.exchange.shape = 2
        >>> model.pass_actualexchange_v1()
        >>> outlets.exchange
        exchange(-2.0, 2.0)
    """

    REQUIREDSEQUENCES = (exch_fluxes.ActualExchange,)
    RESULTSEQUENCES = (exch_outlets.Exchange,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.exchange[0] = -flu.actualexchange
        out.exchange[1] = flu.actualexchange


class Pick_OriginalInput_V1(modeltools.Method):
    r"""Update |OriginalInput| based on |Total|.

    Basic equation:
      :math:`OriginalInput = \sum Total`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> inlets.total.shape = 2
        >>> inlets.total = 2.0, 4.0
        >>> model.pick_originalinput_v1()
        >>> fluxes.originalinput
        originalinput(6.0)
    """

    REQUIREDSEQUENCES = (exch_inlets.Total,)
    RESULTSEQUENCES = (exch_fluxes.OriginalInput,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.originalinput = 0.0
        for idx in range(inl.len_total):
            flu.originalinput += inl.total[idx]


class Calc_AdjustedInput_V1(modeltools.Method):
    r"""Adjust the original input data.

    Basic equation:
        :math:`AdjustedInput = max(OriginalInput + Delta, \ Minimum)`

    Examples:

        The degree of the input adjustment may vary monthly.  Hence, we must define a
        concrete initialisation period for the following examples:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-03-30", "2000-04-03", "1d"
        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> derived.moy.update()

        Negative |Delta| values correspond to decreasing input:

        >>> delta.mar = -1.0
        >>> minimum(0.0)
        >>> model.idx_sim = pub.timegrids.init["2000-03-31"]
        >>> fluxes.originalinput = 1.5
        >>> model.calc_adjustedinput_v1()
        >>> fluxes.adjustedinput
        adjustedinput(0.5)

        The adjusted input values are never smaller than the threshold value defined
        by parameter |Minimum|:

        >>> minimum(1.0)
        >>> model.calc_adjustedinput_v1()
        >>> fluxes.adjustedinput
        adjustedinput(1.0)

        Positive |Delta| values correspond to increasing input:

        >>> model.idx_sim = pub.timegrids.init["2000-04-01"]
        >>> delta.apr = 1.0
        >>> fluxes.originalinput = 0.5
        >>> model.calc_adjustedinput_v1()
        >>> fluxes.adjustedinput
        adjustedinput(1.5)
    """

    CONTROLPARAMETERS = (exch_control.Delta, exch_control.Minimum)
    DERIVEDPARAMETERS = (exch_derived.MOY,)
    REQUIREDSEQUENCES = (exch_fluxes.OriginalInput,)
    RESULTSEQUENCES = (exch_fluxes.AdjustedInput,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.adjustedinput = flu.originalinput + con.delta[der.moy[model.idx_sim]]
        flu.adjustedinput = max(flu.adjustedinput, con.minimum)


class Calc_Outputs_V1(modeltools.Method):
    """Calculate the output via interpolation or extrapolation.

    Examples:

        For example, assume a weir directing all discharge into `branch1` until
        reaching the capacity limit of 2 m³/s.  |exch_branch_hbv96| redirects the
        discharge exceeding this threshold to `branch2`:

        >>> from hydpy.models.exch_branch_hbv96 import *
        >>> parameterstep()
        >>> xpoints(0.0, 2.0, 4.0)
        >>> ypoints(branch1=[0.0, 2.0, 2.0],
        ...         branch2=[0.0, 0.0, 2.0])
        >>> derived.nmbbranches.update()
        >>> derived.nmbpoints.update()

        Low discharge example (linear interpolation between the first two supporting
        point pairs):

        >>> fluxes.adjustedinput = 1.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=1.0,
                branch2=0.0)

        Medium discharge example (linear interpolation between the second two
        supporting point pairs):

        >>> fluxes.adjustedinput = 3.0
        >>> model.calc_outputs_v1()
        >>> print(fluxes.outputs)
        outputs(branch1=2.0,
                branch2=1.0)

        High discharge example (linear extrapolation beyond the second two supporting
        point pairs):

        >>> fluxes.adjustedinput = 5.0
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=2.0,
                branch2=3.0)

        Non-monotonous relationships and balance violations are allowed:

        >>> xpoints(0.0, 2.0, 4.0, 6.0)
        >>> ypoints(branch1=[0.0, 2.0, 0.0, 0.0],
        ...         branch2=[0.0, 0.0, 2.0, 4.0])
        >>> derived.nmbbranches.update()
        >>> derived.nmbpoints.update()
        >>> fluxes.adjustedinput = 7.0
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=0.0,
                branch2=5.0)
    """

    CONTROLPARAMETERS = (exch_control.XPoints, exch_control.YPoints)
    DERIVEDPARAMETERS = (exch_derived.NmbPoints, exch_derived.NmbBranches)
    REQUIREDSEQUENCES = (exch_fluxes.AdjustedInput,)
    RESULTSEQUENCES = (exch_fluxes.Outputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        # Search for the index of the two relevant x points...
        for pdx in range(1, der.nmbpoints):
            if con.xpoints[pdx] > flu.adjustedinput:
                break
        # ...and use it for linear interpolation (or extrapolation).
        d_x = flu.adjustedinput
        for bdx in range(der.nmbbranches):
            d_x0 = con.xpoints[pdx - 1]
            d_dx = con.xpoints[pdx] - d_x0
            d_y0 = con.ypoints[bdx, pdx - 1]
            d_dy = con.ypoints[bdx, pdx] - d_y0
            flu.outputs[bdx] = (d_x - d_x0) * d_dy / d_dx + d_y0


class Calc_Y_V1(modeltools.Method):
    """Use an interpolation function to calculate the result.

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> from hydpy import PPoly
        >>> x2y(PPoly.from_data([0.0, 1.0], [2.0, 4.0]))
        >>> factors.x = 0.5
        >>> model.calc_y_v1()
        >>> factors.y
        y(3.0)
    """

    CONTROLPARAMETERS = (exch_control.X2Y,)
    REQUIREDSEQUENCES = (exch_factors.X,)
    RESULTSEQUENCES = (exch_factors.Y,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        con.x2y.inputs[0] = fac.x
        con.x2y.calculate_values()
        fac.y = con.x2y.outputs[0]


class Pass_Outputs_V1(modeltools.Method):
    """Update |Branched| based on |Outputs|.

    Basic equation:
      :math:`Branched_i = Outputs_i`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> derived.nmbbranches(2)
        >>> fluxes.outputs.shape = 2
        >>> fluxes.outputs = 2.0, 4.0
        >>> outlets.branched.shape = 2
        >>> model.pass_outputs_v1()
        >>> outlets.branched
        branched(2.0, 4.0)
    """

    DERIVEDPARAMETERS = (exch_derived.NmbBranches,)
    REQUIREDSEQUENCES = (exch_fluxes.Outputs,)
    RESULTSEQUENCES = (exch_outlets.Branched,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        for bdx in range(der.nmbbranches):
            out.branched[bdx] = flu.outputs[bdx]


class Pass_Y_V1(modeltools.Method):
    """Pass the result data to an arbitrary number of sender nodes.

    Basic equation:
      :math:`Y_{senders} = Y_{factors}`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> factors.y = 3.0
        >>> senders.y.shape = 2
        >>> model.pass_y_v1()
        >>> senders.y
        y(3.0, 3.0)
    """

    REQUIREDSEQUENCES = (exch_factors.Y,)
    RESULTSEQUENCES = (exch_senders.Y,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        sen = model.sequences.senders.fastaccess
        for i in range(sen.len_y):
            sen.y[i] = fac.y


class Get_WaterLevel_V1(modeltools.Method):
    """Return the water level in m.

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> logs.loggedwaterlevel = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_waterlevel_v1())
        2.0
    """

    REQUIREDSEQUENCES = (exch_logs.LoggedWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        log = model.sequences.logs.fastaccess
        return log.loggedwaterlevel[0]


class Determine_Y_V1(modeltools.AutoMethod):
    """Interface method for determining the result."""

    SUBMETHODS = (Pick_X_V1, Calc_Y_V1)
    CONTROLPARAMETERS = (exch_control.ObserverNodes, exch_control.X2Y)
    REQUIREDSEQUENCES = (exch_observers.X,)
    RESULTSEQUENCES = (exch_factors.X, exch_factors.Y)


class Get_Y_V1(modeltools.Method):
    """Return the result.

    >>> from hydpy.models.exch import *
    >>> parameterstep()
    >>> factors.y = 2.0
    >>> model.get_y_v1()
    2.0
    """

    REQUIREDSEQUENCES = (exch_factors.Y,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.y


class Model(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """|exch.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Exch")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = (Pick_OriginalInput_V1,)
    OBSERVER_METHODS = (Pick_X_V1,)
    RECEIVER_METHODS = (Pick_LoggedWaterLevel_V1, Pick_LoggedWaterLevels_V1)
    RUN_METHODS = (
        Update_WaterLevels_V1,
        Calc_DeltaWaterLevel_V1,
        Calc_PotentialExchange_V1,
        Calc_ActualExchange_V1,
        Calc_AdjustedInput_V1,
        Calc_Outputs_V1,
        Calc_Y_V1,
    )
    INTERFACE_METHODS = (Get_WaterLevel_V1, Determine_Y_V1, Get_Y_V1)
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_ActualExchange_V1, Pass_Outputs_V1, Pass_Y_V1)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
