# pylint: disable=missing-module-docstring

from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.models.exch import exch_control
from hydpy.models.exch import exch_derived
from hydpy.models.exch import exch_inputs
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
    def __call__(model: modeltools.Model, /) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedwaterlevel[0] = rec.waterlevel


class Pick_LoggedWaterLevels_V1(modeltools.Method):
    """Pick the logged water levels from two receiver nodes.

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
    def __call__(model: modeltools.Model, /) -> None:
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
    def __call__(model: modeltools.Model, /) -> None:
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
    def __call__(model: modeltools.Model, /) -> None:
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(2):
            fac.waterlevels[idx] = log.loggedwaterlevels[idx]


class Calc_DeltaWaterLevel_V1(modeltools.Method):
    r"""Calculate the effective difference between both water levels.

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
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        wl0: float = max(fac.waterlevels[0], con.crestheight)
        wl1: float = max(fac.waterlevels[1], con.crestheight)
        fac.deltawaterlevel = wl0 - wl1


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
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if fac.deltawaterlevel >= 0.0:
            dwl: float = fac.deltawaterlevel
            sig: float = 1.0
        else:
            dwl = -fac.deltawaterlevel
            sig = -1.0
        flu.potentialexchange = sig * (
            con.flowcoefficient * con.crestwidth * dwl**con.flowexponent
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
    def __call__(model: modeltools.Model, /) -> None:
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
    def __call__(model: modeltools.Model, /) -> None:
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
    def __call__(model: modeltools.Model, /) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.originalinput = 0.0
        for idx in range(inl.len_total):
            flu.originalinput += inl.total[idx]


class Pick_Input_V1(modeltools.Method):
    r"""Sum all individual input values.

    Basic equation:
      :math:`Input = \sum Total`

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> inlets.total.shape = 2
        >>> inlets.total = 2.0, 4.0
        >>> model.pick_input_v1()
        >>> fluxes.input_
        input_(6.0)
    """

    REQUIREDSEQUENCES = (exch_inlets.Total,)
    RESULTSEQUENCES = (exch_fluxes.Input_,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.input_ = 0.0
        for idx in range(inl.len_total):
            flu.input_ += inl.total[idx]


class Pick_Inflow_V1(modeltools.Method):
    r"""Sum all individual inflow values.

    Basic equation:
      .. math::
        Inflow_{fluxes} = \sum Inflow_{inputs}

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> inlets.inflow.shape = 2
        >>> inlets.inflow = 2.0, 4.0
        >>> model.pick_inflow_v1()
        >>> fluxes.inflow
        inflow(6.0)
    """

    REQUIREDSEQUENCES = (exch_inlets.Inflow,)
    RESULTSEQUENCES = (exch_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.inflow = 0.0
        for idx in range(inl.len_inflow):
            flu.inflow += inl.inflow[idx]


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
    def __call__(model: modeltools.Model, /) -> None:
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

        >>> from hydpy.core.exceptiontools import ignore_deprecations
        >>> from hydpy.models.exch_branch_hbv96 import *
        >>> with ignore_deprecations():
        ...     parameterstep()
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
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        # Search for the index of the two relevant x points...
        for pdx in range(1, der.nmbpoints):
            if con.xpoints[pdx] > flu.adjustedinput:
                break
        # ...and use it for linear interpolation (or extrapolation).
        x: float = flu.adjustedinput
        for bdx in range(der.nmbbranches):
            x0: float = con.xpoints[pdx - 1]
            dx: float = con.xpoints[pdx] - x0
            y0: float = con.ypoints[bdx, pdx - 1]
            dy: float = con.ypoints[bdx, pdx] - y0
            flu.outputs[bdx] = (x - x0) * dy / dx + y0


class Calc_Y_V1(modeltools.Method):
    """Use an interpolation function to calculate the result.

    Example:

        >>> from hydpy.models.exch import *
        >>> parameterstep()
        >>> from hydpy import PPoly
        >>> x2y(PPoly(xs=[0.0, 1.0], ys=[2.0, 4.0]))
        >>> factors.x = 0.5
        >>> model.calc_y_v1()
        >>> factors.y
        y(3.0)
    """

    CONTROLPARAMETERS = (exch_control.X2Y,)
    REQUIREDSEQUENCES = (exch_factors.X,)
    RESULTSEQUENCES = (exch_factors.Y,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess

        con.x2y.inputs[0] = fac.x
        con.x2y.calculate_values()
        fac.y = con.x2y.outputs[0]


class Pass_ActualTransfer_StreamOutflow_V1(modeltools.Method):
    """Calculate the actual water transfer and remaining stream outflow based on
    external transfer requests (if available) or based on internal transfer
    calculations (as a fallback).

    Basic equations:
      .. math::
        ActualTransfer = RequestedTransfer \\
        StreamOutflow = Inflow - ActualTransfer

    Examples:

        We prepare a 15-day simulation period and set up a |UnitTest| instance to
        automatically use method |Pass_ActualTransfer_StreamOutflow_V1| with the
        corresponding input values (each example refers to the next day, starting
        with January 1):

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-16", "1d"
        >>> from hydpy.models.exch_branch_io import *
        >>> parameterstep()
        >>> derived.toy.update()
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model,
        ...     model.pass_actualtransfer_streamoutflow_v1,
        ...     last_example=14,
        ...     parseqs=(
        ...         fluxes.inflow,
        ...         inputs.requestedtransfer,
        ...         outlets.actualtransfer,
        ...         outlets.streamoutflow,
        ...     ),
        ...     first_idx_sim=0,
        ... )

        In all of the following examples, the inflow increases linearly from -4 to
        9 m³/s:

        >>> test.nexts.inflow = range(-4, 10)

        For the first example, we set all requested transfer values to |numpy.nan| or
        |numpy.inf| (the latter, positive and negative):

        >>> test.nexts.requestedtransfer = 12 * [nan] + [inf, -inf]

        All of the given values have similar meaning. They either indicate that
        information about the requested transfer is missing (typical meaning
        |numpy.nan|) or that it is intentionally not passed (we use this interpretation
        for |numpy.inf| here).  The choice between them might matter in applications,
        for example when loading affected time series with the |Options.checkseries|
        option enabled.  However, |Pass_ActualTransfer_StreamOutflow_V1| reacts the
        same way by falling back to its internal transfer calculations.

        We now configure these calculations by defining the target nodes and their
        season-dependent interpolation rules, which determine which target node gets
        which proportion of the available inflow (see the documentation on the
        parameters |Targets| and |FlowTransferRules| for more explanations and
        configuration options):

        >>> targets(stream="river", transfer="diversion")
        >>> flowtransferrules(
        ...     toy_01_01_12=PPoly(xs=[-1.0, 0.0, 1.0], ys=[0.0, 0.0, 0.5]),
        ...     toy_01_04_12=PPoly(xs=[-1.0, 0.0, 1.0], ys=[0.0, 0.0, 0.5]),
        ...     toy_01_14_12=PPoly(xs=[0.0], ys=[0.0]),
        ... )
        >>> derived.streamindex.update()

        Note that the first interpolation rule, which solely applies for the first four
        days (due to its double definition) lets "negative inflow" (reverse flow) pass
        unhindered through the main stream and transfers half of the "positive inflow"
        (normal flow).  Between the fourth and fourteenth day, the second rule, which
        does not order any water transfer, becomes gradually more important.  Because
        of the "normal" way to configure |FlowTransferRules| via |PPoly| instances
        instead of |PPolys| instances, the water balance (:math:`Inflow =
        ActualTransfer + StreamOutflow`) is automatically kept:

        >>> test()
        | ex. | inflow | requestedtransfer | actualtransfer | streamoutflow |
        ---------------------------------------------------------------------
        |   1 |   -4.0 |               nan |            0.0 |          -4.0 |
        |   2 |   -3.0 |               nan |            0.0 |          -3.0 |
        |   3 |   -2.0 |               nan |            0.0 |          -2.0 |
        |   4 |   -1.0 |               nan |            0.0 |          -1.0 |
        |   5 |    0.0 |               nan |            0.0 |           0.0 |
        |   6 |    1.0 |               nan |            0.4 |           0.6 |
        |   7 |    2.0 |               nan |            0.7 |           1.3 |
        |   8 |    3.0 |               nan |            0.9 |           2.1 |
        |   9 |    4.0 |               nan |            1.0 |           3.0 |
        |  10 |    5.0 |               nan |            1.0 |           4.0 |
        |  11 |    6.0 |               nan |            0.9 |           5.1 |
        |  12 |    7.0 |               nan |            0.7 |           6.3 |
        |  13 |    8.0 |               inf |            0.4 |           7.6 |
        |  14 |    9.0 |              -inf |            0.0 |           9.0 |

        As soon as we provide external transfer requests, parameter |FlowTransferRules|
        becomes obsolete (positive transfers correspond to withdrawals from the stream
        and negative transfers correspond to supplies to the stream):

        >>> test.nexts.requestedtransfer = 7 * [4.0, -4.0]

        Instead, parameters |MinStream| and |MaxStream| come into play, restricting
        withdrawals and supplies, respectively (note that they do not affect the
        fallback calculations based on |FlowTransferRules|).  We first set them to
        minus infinity and infinity, so the transfer is completely unrestricted:

        >>> minstream(-numpy.inf)
        >>> maxstream(numpy.inf)

        Without restrictions, the basic equation applies without modification:

        >>> test()
        | ex. | inflow | requestedtransfer | actualtransfer | streamoutflow |
        ---------------------------------------------------------------------
        |   1 |   -4.0 |               4.0 |            4.0 |          -8.0 |
        |   2 |   -3.0 |              -4.0 |           -4.0 |           1.0 |
        |   3 |   -2.0 |               4.0 |            4.0 |          -6.0 |
        |   4 |   -1.0 |              -4.0 |           -4.0 |           3.0 |
        |   5 |    0.0 |               4.0 |            4.0 |          -4.0 |
        |   6 |    1.0 |              -4.0 |           -4.0 |           5.0 |
        |   7 |    2.0 |               4.0 |            4.0 |          -2.0 |
        |   8 |    3.0 |              -4.0 |           -4.0 |           7.0 |
        |   9 |    4.0 |               4.0 |            4.0 |           0.0 |
        |  10 |    5.0 |              -4.0 |           -4.0 |           9.0 |
        |  11 |    6.0 |               4.0 |            4.0 |           2.0 |
        |  12 |    7.0 |              -4.0 |           -4.0 |          11.0 |
        |  13 |    8.0 |               4.0 |            4.0 |           4.0 |
        |  14 |    9.0 |              -4.0 |           -4.0 |          13.0 |

        For the remaining examples, we want the water transfer not to cause stream
        outflow values below 3 and above 6 m³/s:

        >>> minstream(3.0)
        >>> maxstream(6.0)

        First, we focus on positive transfers (withdrawals), so that only parameter
        |MinStream| is used:

        >>> test.nexts.requestedtransfer = 14 * [2.0]

        The exact behaviour of preventing excessive withdrawals depends on parameter
        |KeepWaterBalance|.  If it is |True|, the actual transfer is limited to the
        inflow exceeding |MinStream|.  However, inflow values already below |MinStream|
        are not automatically increased by supplies, meaning |ActualTransfer| is at
        most decreased to zero and not to negative values:

        >>> keepwaterbalance(True)
        >>> test()
        | ex. | inflow | requestedtransfer | actualtransfer | streamoutflow |
        ---------------------------------------------------------------------
        |   1 |   -4.0 |               2.0 |            0.0 |          -4.0 |
        |   2 |   -3.0 |               2.0 |            0.0 |          -3.0 |
        |   3 |   -2.0 |               2.0 |            0.0 |          -2.0 |
        |   4 |   -1.0 |               2.0 |            0.0 |          -1.0 |
        |   5 |    0.0 |               2.0 |            0.0 |           0.0 |
        |   6 |    1.0 |               2.0 |            0.0 |           1.0 |
        |   7 |    2.0 |               2.0 |            0.0 |           2.0 |
        |   8 |    3.0 |               2.0 |            0.0 |           3.0 |
        |   9 |    4.0 |               2.0 |            1.0 |           3.0 |
        |  10 |    5.0 |               2.0 |            2.0 |           3.0 |
        |  11 |    6.0 |               2.0 |            2.0 |           4.0 |
        |  12 |    7.0 |               2.0 |            2.0 |           5.0 |
        |  13 |    8.0 |               2.0 |            2.0 |           6.0 |
        |  14 |    9.0 |               2.0 |            2.0 |           7.0 |

        If |KeepWaterBalance| is |False|, |StreamOutflow| is reduced when necessary,
        but |ActualTransfer| is always identical to |RequestedTransfer| (see the
        explanation in the documentation of parameter |KeepWaterBalance|):

        >>> keepwaterbalance(False)
        >>> test()
        | ex. | inflow | requestedtransfer | actualtransfer | streamoutflow |
        ---------------------------------------------------------------------
        |   1 |   -4.0 |               2.0 |            2.0 |          -4.0 |
        |   2 |   -3.0 |               2.0 |            2.0 |          -3.0 |
        |   3 |   -2.0 |               2.0 |            2.0 |          -2.0 |
        |   4 |   -1.0 |               2.0 |            2.0 |          -1.0 |
        |   5 |    0.0 |               2.0 |            2.0 |           0.0 |
        |   6 |    1.0 |               2.0 |            2.0 |           1.0 |
        |   7 |    2.0 |               2.0 |            2.0 |           2.0 |
        |   8 |    3.0 |               2.0 |            2.0 |           3.0 |
        |   9 |    4.0 |               2.0 |            2.0 |           3.0 |
        |  10 |    5.0 |               2.0 |            2.0 |           3.0 |
        |  11 |    6.0 |               2.0 |            2.0 |           4.0 |
        |  12 |    7.0 |               2.0 |            2.0 |           5.0 |
        |  13 |    8.0 |               2.0 |            2.0 |           6.0 |
        |  14 |    9.0 |               2.0 |            2.0 |           7.0 |

        The restriction of |StreamOutflow| to |MaxStream| for negative transfer
        requests (supplies) is exactly the opposite:

        >>> test.nexts.requestedtransfer = 14 * [-2.0]

        >>> keepwaterbalance(True)
        >>> test()
        | ex. | inflow | requestedtransfer | actualtransfer | streamoutflow |
        ---------------------------------------------------------------------
        |   1 |   -4.0 |              -2.0 |           -2.0 |          -2.0 |
        |   2 |   -3.0 |              -2.0 |           -2.0 |          -1.0 |
        |   3 |   -2.0 |              -2.0 |           -2.0 |           0.0 |
        |   4 |   -1.0 |              -2.0 |           -2.0 |           1.0 |
        |   5 |    0.0 |              -2.0 |           -2.0 |           2.0 |
        |   6 |    1.0 |              -2.0 |           -2.0 |           3.0 |
        |   7 |    2.0 |              -2.0 |           -2.0 |           4.0 |
        |   8 |    3.0 |              -2.0 |           -2.0 |           5.0 |
        |   9 |    4.0 |              -2.0 |           -2.0 |           6.0 |
        |  10 |    5.0 |              -2.0 |           -1.0 |           6.0 |
        |  11 |    6.0 |              -2.0 |            0.0 |           6.0 |
        |  12 |    7.0 |              -2.0 |            0.0 |           7.0 |
        |  13 |    8.0 |              -2.0 |            0.0 |           8.0 |
        |  14 |    9.0 |              -2.0 |            0.0 |           9.0 |

        >>> keepwaterbalance(False)
        >>> test()
        | ex. | inflow | requestedtransfer | actualtransfer | streamoutflow |
        ---------------------------------------------------------------------
        |   1 |   -4.0 |              -2.0 |           -2.0 |          -2.0 |
        |   2 |   -3.0 |              -2.0 |           -2.0 |          -1.0 |
        |   3 |   -2.0 |              -2.0 |           -2.0 |           0.0 |
        |   4 |   -1.0 |              -2.0 |           -2.0 |           1.0 |
        |   5 |    0.0 |              -2.0 |           -2.0 |           2.0 |
        |   6 |    1.0 |              -2.0 |           -2.0 |           3.0 |
        |   7 |    2.0 |              -2.0 |           -2.0 |           4.0 |
        |   8 |    3.0 |              -2.0 |           -2.0 |           5.0 |
        |   9 |    4.0 |              -2.0 |           -2.0 |           6.0 |
        |  10 |    5.0 |              -2.0 |           -2.0 |           6.0 |
        |  11 |    6.0 |              -2.0 |           -2.0 |           6.0 |
        |  12 |    7.0 |              -2.0 |           -2.0 |           7.0 |
        |  13 |    8.0 |              -2.0 |           -2.0 |           8.0 |
        |  14 |    9.0 |              -2.0 |           -2.0 |           9.0 |

        |MinStream| and |MaxStream| can be identical:

        >>> minstream(4.0)
        >>> maxstream(4.0)
        >>> keepwaterbalance(True)
        >>> test.nexts.requestedtransfer = 7 * [2.0, -2.0]
        >>> test()
        | ex. | inflow | requestedtransfer | actualtransfer | streamoutflow |
        ---------------------------------------------------------------------
        |   1 |   -4.0 |               2.0 |            0.0 |          -4.0 |
        |   2 |   -3.0 |              -2.0 |           -2.0 |          -1.0 |
        |   3 |   -2.0 |               2.0 |            0.0 |          -2.0 |
        |   4 |   -1.0 |              -2.0 |           -2.0 |           1.0 |
        |   5 |    0.0 |               2.0 |            0.0 |           0.0 |
        |   6 |    1.0 |              -2.0 |           -2.0 |           3.0 |
        |   7 |    2.0 |               2.0 |            0.0 |           2.0 |
        |   8 |    3.0 |              -2.0 |           -1.0 |           4.0 |
        |   9 |    4.0 |               2.0 |            0.0 |           4.0 |
        |  10 |    5.0 |              -2.0 |            0.0 |           5.0 |
        |  11 |    6.0 |               2.0 |            2.0 |           4.0 |
        |  12 |    7.0 |              -2.0 |            0.0 |           7.0 |
        |  13 |    8.0 |               2.0 |            2.0 |           6.0 |
        |  14 |    9.0 |              -2.0 |            0.0 |           9.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        exch_control.MinStream,
        exch_control.MaxStream,
        exch_control.KeepWaterBalance,
        exch_control.FlowTransferRules,
    )
    DERIVEDPARAMETERS = (exch_derived.TOY, exch_derived.StreamIndex)
    REQUIREDSEQUENCES = (exch_fluxes.Inflow, exch_inputs.RequestedTransfer)
    RESULTSEQUENCES = (exch_outlets.ActualTransfer, exch_outlets.StreamOutflow)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:

        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess

        excess: float
        lack: float
        if modelutils.isnan(inp.requestedtransfer) or modelutils.isinf(
            inp.requestedtransfer
        ):
            con.flowtransferrules.inputs[0] = flu.inflow
            con.flowtransferrules.calculate_values(der.toy[model.idx_sim])
            out.streamoutflow = con.flowtransferrules.outputs[der.streamindex]
            out.actualtransfer = con.flowtransferrules.outputs[1 - der.streamindex]
        elif inp.requestedtransfer > 0.0 and inp.requestedtransfer > (
            excess := flu.inflow - con.minstream
        ):
            if con.keepwaterbalance:
                out.actualtransfer = max(excess, 0.0)
                out.streamoutflow = flu.inflow - out.actualtransfer
            else:
                out.actualtransfer = inp.requestedtransfer
                out.streamoutflow = min(flu.inflow, con.minstream)
        elif inp.requestedtransfer < 0.0 and -inp.requestedtransfer > (
            lack := con.maxstream - flu.inflow
        ):
            if con.keepwaterbalance:
                out.actualtransfer = -max(lack, 0.0)
                out.streamoutflow = flu.inflow - out.actualtransfer
            else:
                out.actualtransfer = inp.requestedtransfer
                out.streamoutflow = max(flu.inflow, con.maxstream)
        else:
            out.actualtransfer = inp.requestedtransfer
            out.streamoutflow = flu.inflow - inp.requestedtransfer


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
    def __call__(model: modeltools.Model, /) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        for bdx in range(der.nmbbranches):
            out.branched[bdx] = flu.outputs[bdx]


class Pass_Branched_V1(modeltools.Method):
    r"""Branch the current input by applying the (seasonally varying) interpolation
    rules.

    Basic equation:
      :math:`Branched_i = Rules_i(Input)`

    Example:

        We define two different branching rules for January 1 and 2 (see the
        documentation on parameter |Rules| for more information):

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
        >>> from hydpy.models.exch_branch_rules import *
        >>> parameterstep()
        >>> rules(
        ...     toy_01_01_12=PPolys(
        ...         a=PPoly(xs=[0.0, 1.0], ys=[0.0, 1.0]),
        ...         b=PPolys.REST,
        ...     ),
        ...     toy_01_02_12=PPolys(
        ...         a=PPolys.REST,
        ...         b=PPoly(xs=[0.0], ys=[1.0]),
        ...     ),
        ... )
        >>> derived.toy.update()
        >>> outlets.branched.shape = 2
        >>> fluxes.input_ = 3.0

        >>> model.idx_sim = pub.timegrids.init["2000-01-01"]
        >>> model.pass_branched_v1()
        >>> outlets.branched
        branched(3.0, 0.0)

        >>> model.idx_sim = pub.timegrids.init["2000-01-02"]
        >>> model.pass_branched_v1()
        >>> outlets.branched
        branched(2.0, 1.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (exch_control.Rules,)
    DERIVEDPARAMETERS = (exch_derived.TOY,)
    REQUIREDSEQUENCES = (exch_fluxes.Input_,)
    RESULTSEQUENCES = (exch_outlets.Branched,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        con.rules.inputs[0] = flu.input_
        con.rules.calculate_values(der.toy[model.idx_sim])
        for i in range(out.len_branched):
            out.branched[i] = con.rules.outputs[i]


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
    def __call__(model: modeltools.Model, /) -> None:
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
    def __call__(model: modeltools.Model, /) -> float:
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
    def __call__(model: modeltools.Model, /) -> float:
        fac = model.sequences.factors.fastaccess

        return fac.y


class Model(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """|exch.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Exch")
    __HYDPY_ROOTMODEL__ = None

    nodenames: list[str] = []
    targetnames: tuple[str, ...] = ()

    INLET_METHODS = (Pick_OriginalInput_V1, Pick_Input_V1, Pick_Inflow_V1)
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
    OUTLET_METHODS = (
        Pass_ActualExchange_V1,
        Pass_Outputs_V1,
        Pass_Branched_V1,
        Pass_ActualTransfer_StreamOutflow_V1,
        Pass_Y_V1,
    )
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
