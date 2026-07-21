# pylint: disable=missing-module-docstring
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import statcorrinterfaces
from hydpy.models.statcorr import statcorr_control
from hydpy.models.statcorr import statcorr_inputs
from hydpy.models.statcorr import statcorr_inlets
from hydpy.models.statcorr import statcorr_outlets
from hydpy.models.statcorr import statcorr_fluxes
from hydpy.models.statcorr import statcorr_logs
from hydpy.models.statcorr import statcorr_states
from hydpy.models.statcorr import statcorr_derived


class Pick_Inflow_V1(modeltools.Method):
    r"""Sum up the current inflow from all inlet nodes.

    Basic equation:
      :math:`Inflow = \sum Q`

    Example:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> inlets.q.shape = 2
        >>> inlets.q = 2.0, 4.0
        >>> model.pick_inflow_v1()
        >>> fluxes.inflow
        inflow(6.0)
    """

    REQUIREDSEQUENCES = (statcorr_inlets.Q,)
    RESULTSEQUENCES = (statcorr_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.inflow = 0.0
        for idx in range(inl.len_q):
            flu.inflow += inl.q[idx]


class Calc_OutputCorr_V1(modeltools.Method):
    """Apply each |OutputCorrModel_V1| submodel to the current simulated and observed
    discharge and combine their results into the corrected discharge.

    This method orchestrates one or more submodels of identical interface type:

    1. The current simulated discharge (|Inflow|) and observed discharge
       (|Discharge|) are passed to each attached |OutputCorrModel_V1| submodel
       via |OutputCorrModel_V1.set_simulateddischarge| and
       |OutputCorrModel_V1.set_observeddischarge|.  While |Options.simulationmode|
       equals `forecast`, |Calc_OutputCorr_V1| passes |numpy.nan| instead of the
       actual value of |Discharge|, regardless of whether an observation is
       available.  This relies on the assumption that a previous `historical`
       simulation run already logged all relevant past observations and
       simulations (read in as conditions).
    2. Each submodel computes its corrected discharge via
       |OutputCorrModel_V1.determine_outputcorrection|.
    3. The corrected output of the *last* attached submodel is taken as
       |CorrectedQ|.  When no submodel is attached, |CorrectedQ| equals
       |Inflow|.  Since each submodel decides for itself, based on its own
       |CorrNQ|, |CorrMQ|, and |CorrHQ| flags, whether the current NQ, MQ, or
       HQ flow condition warrants a correction (passing through the current
       simulated discharge unchanged otherwise), attaching several submodels
       configured for mutually exclusive flow ranges automatically lets only
       the one responsible for the current flow condition take effect.

    Examples:

        Without any attached submodel, the corrected discharge equals the inflow:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> fluxes.inflow = 2.0
        >>> inputs.discharge = 3.0
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(2.0)

        With a single attached |statcorr_arima010| submodel, the corrected
        discharge is the inflow plus the most recent residual (here:
        ``3.0 - 2.0 = 1.0``, applied to the new inflow ``2.5``).  We enable
        correction for all discharge ranges and set |QminQmax| to zero so that
        the LARSIM stationarity check never suppresses the correction:

        >>> def configure(submodel):
        ...     submodel.parameters.control.corrnq(True)
        ...     submodel.parameters.control.corrmq(True)
        ...     submodel.parameters.control.corrhq(True)
        ...     submodel.parameters.control.limitnqm(0.0)
        ...     submodel.parameters.control.limitmqh(100.0)
        ...     submodel.parameters.control.evaluationwindow(2)
        ...     submodel.parameters.control.maxresiduallookback(3)
        ...     submodel.parameters.control.maxabsoluteshift(100.0)
        ...     submodel.parameters.control.maxrelativeshift(1000.0)
        ...     submodel.parameters.control.residualaveragingwindow(0)
        ...     submodel.parameters.control.residualtransitiontime(0)
        ...     submodel.parameters.control.qminqmax(0.0)
        ...     submodel.parameters.control.nqmstationaritywindow(2)
        ...     submodel.parameters.control.linearreductiontime(1, 1)

        >>> loggingwindow(2)
        >>> nmboutputcorrmodels(1)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=0
        ... ) as submodel:
        ...     configure(submodel)
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(3.0)
        >>> from numpy import nan
        >>> fluxes.inflow = 2.5
        >>> inputs.discharge = nan
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(3.5)

        With two attached submodels of the same type, the second one's output
        wins:

        >>> nmboutputcorrmodels(2)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=0
        ... ) as submodel:
        ...     configure(submodel)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=1
        ... ) as submodel:
        ...     configure(submodel)
        >>> fluxes.inflow = 2.5
        >>> inputs.discharge = 4.0
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(4.0)

        While |Options.simulationmode| equals ``forecast``, |Calc_OutputCorr_V1|
        ignores the actual value of |Discharge| and passes |numpy.nan| to the
        submodels instead, relying on their logic to
        keep applying the most recently logged residual (see |statcorr_arima010|
        for the mechanism and the module docstring of |statcorr_main| for the
        assumed workflow of a preceding `historical` run).  |Calc_OutputCorr_V1|
        also forwards the current |Options.simulationmode| to each submodel's
        |OutputCorrModel_V1.determine_outputcorrection| call (see
        |Determine_OutputCorrection_V1|), so submodels never need to inspect the
        global option themselves.  |Parameters.update| (usually triggered via
        |HydPy.update_parameters|) must be called after changing
        |Options.simulationmode| for |IsForecastMode| (and hence
        |Calc_OutputCorr_V1|) to take effect; deliberately, this does *not*
        require (or recommend) calling |Model.update_parameters|, which would
        also needlessly re-run the submodels' attachment/initialisation logic
        and wipe their logged history:

        >>> loggingwindow(3)
        >>> nmboutputcorrmodels(1)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=0
        ... ) as submodel:
        ...     configure(submodel)
        >>> model.parameters.update()

        Two `historical` steps establish a residual of ``0.5``:

        >>> fluxes.inflow = 1.0
        >>> inputs.discharge = 1.5
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(1.5)
        >>> fluxes.inflow = 2.0
        >>> inputs.discharge = 2.5
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(2.5)

        Switching to `forecast` mode and feeding an implausible |Discharge|
        value (``999.0``, which would dominate the result if it were not
        ignored) still reproduces the persisted residual of ``0.5``:

        >>> from hydpy import pub
        >>> with pub.options.simulationmode("forecast"):
        ...     model.parameters.update()
        ...     fluxes.inflow = 3.0
        ...     inputs.discharge = 999.0
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(3.5)
        >>> with pub.options.simulationmode("forecast"):
        ...     model.parameters.update()
        ...     fluxes.inflow = 4.0
        ...     inputs.discharge = 999.0
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(4.5)

        Once the last real observation drops out of the three-step logging
        window, no correction is applied anymore:

        >>> with pub.options.simulationmode("forecast"):
        ...     model.parameters.update()
        ...     fluxes.inflow = 5.0
        ...     inputs.discharge = 999.0
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(5.0)
    """

    SUBMODELINTERFACES = (statcorrinterfaces.OutputCorrModel_V1,)
    DERIVEDPARAMETERS = (statcorr_derived.IsForecastMode,)
    REQUIREDSEQUENCES = (statcorr_fluxes.Inflow, statcorr_inputs.Discharge)
    RESULTSEQUENCES = (statcorr_fluxes.CorrectedQ,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        inp = model.sequences.inputs.fastaccess
        observeddischarge: float = (
            modelutils.nan if der.isforecastmode else inp.discharge
        )
        flu.correctedq = flu.inflow
        for i in range(model.outputcorrmodels.number):
            if model.outputcorrmodels.typeids[i] == 1:
                cast(
                    statcorrinterfaces.OutputCorrModel_V1,
                    model.outputcorrmodels.submodels[i],
                ).set_simulateddischarge(flu.inflow)
                cast(
                    statcorrinterfaces.OutputCorrModel_V1,
                    model.outputcorrmodels.submodels[i],
                ).set_observeddischarge(observeddischarge)
                cast(
                    statcorrinterfaces.OutputCorrModel_V1,
                    model.outputcorrmodels.submodels[i],
                ).determine_outputcorrection(bool(der.isforecastmode))
                flu.correctedq = cast(
                    statcorrinterfaces.OutputCorrModel_V1,
                    model.outputcorrmodels.submodels[i],
                ).get_correctedoutput()


class Pass_Q_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:
        :math:`Q_{outlets} = Q_{fluxes} + Q_{inputs}`

    |Pass_Q_V1| is used, for example, by |statcorr_test|, not by |statcorr| itself
    (which uses |Pass_CorrectedQ_V1| instead):

    Example:

        >>> from hydpy.models.statcorr_test import *
        >>> parameterstep()
        >>> fluxes.inflow = 2.0
        >>> inputs.discharge = 1.0
        >>> model.pass_q_v1()
        >>> outlets.q
        q(3.0)
    """

    REQUIREDSEQUENCES = (statcorr_fluxes.Inflow, statcorr_inputs.Discharge)
    RESULTSEQUENCES = (statcorr_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        flu = model.sequences.fluxes.fastaccess
        inp = model.sequences.inputs.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q = flu.inflow + inp.discharge


class Pass_CorrectedQ_V1(modeltools.Method):
    """Pass the corrected discharge on to the outlet link sequence, unless
    |PropagateCorrection| is |False|, in which case the uncorrected inflow is
    passed on instead.  Either way, |CorrectedQ| remains available for local
    output at the current gauge.

    Basic equation:
        :math:`Q_{outlets} = CorrectedQ` (if |PropagateCorrection|) or
        :math:`Q_{outlets} = Inflow` (otherwise)

    Examples:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> fluxes.inflow = 1.0
        >>> fluxes.correctedq = 2.0

        >>> propagatecorrection(True)
        >>> model.pass_correctedq_v1()
        >>> outlets.q
        q(2.0)

        >>> propagatecorrection(False)
        >>> model.pass_correctedq_v1()
        >>> outlets.q
        q(1.0)
    """

    CONTROLPARAMETERS = (statcorr_control.PropagateCorrection,)
    REQUIREDSEQUENCES = (statcorr_fluxes.Inflow, statcorr_fluxes.CorrectedQ)
    RESULTSEQUENCES = (statcorr_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q = flu.correctedq if con.propagatecorrection else flu.inflow


class Get_Discharge_V1(modeltools.Method):
    """Get the current measured discharge.

    Example:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> inputs.discharge = 2.0
        >>> from hydpy import round_
        >>> round_(model.get_discharge_v1())
        2.0
    """

    REQUIREDSEQUENCES = (statcorr_inputs.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> float:
        inp = model.sequences.inputs.fastaccess

        return inp.discharge


class Model(modeltools.AdHocModel):
    """|statcorr.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="statcorr")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = (Pick_Inflow_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (Calc_OutputCorr_V1,)
    INTERFACE_METHODS = (Get_Discharge_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_CorrectedQ_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (statcorrinterfaces.OutputCorrModel_V1,)
    SUBMODELS = ()

    outputcorrmodels = modeltools.SubmodelsProperty(
        statcorrinterfaces.OutputCorrModel_V1
    )

    @importtools.prepare_submodel(
        "outputcorrmodels",
        statcorrinterfaces.OutputCorrModel_V1,
        statcorrinterfaces.OutputCorrModel_V1.prepare_nmblogentries,
        dimensionality=1,
    )
    def add_outputcorrmodel_v1(
        self,
        outputcorrmodel: statcorrinterfaces.OutputCorrModel_V1,
        *,
        position: int,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given submodel that follows the |OutputCorrModel_V1|
        interface and propagate the main model's |LoggingWindow| to its internal
        log allocation.

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> loggingwindow(4)
        >>> nmboutputcorrmodels(1)
        >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0):
        ...     pass
        >>> model.outputcorrmodels[0].parameters.derived.nmblogentries
        nmblogentries(4)
        >>> model.outputcorrmodels[0].sequences.logs.loggedsimulateddischarge
        loggedsimulateddischarge(nan, nan, nan, nan)
        """
        nmb = int(self.parameters.control.loggingwindow.value)
        outputcorrmodel.parameters.control.loggingwindow(nmb)
        outputcorrmodel.prepare_nmblogentries(nmb)


class Set_SimulatedDischarge_V1(modeltools.Method):
    """Append the given simulated discharge value to the internal log of simulated
    discharge by shifting the previously buffered values one position to the right
    and storing the new value at position 0.

    Example:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedsimulateddischarge.shape = 3
        >>> logs.loggedsimulateddischarge = 4.0, 3.0, 2.0
        >>> model.set_simulateddischarge_v1(5.0)
        >>> logs.loggedsimulateddischarge
        loggedsimulateddischarge(5.0, 4.0, 3.0)
    """

    DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)
    UPDATEDSEQUENCES = (statcorr_logs.LoggedSimulatedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model, simulateddischarge: float, /) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedsimulateddischarge[idx] = log.loggedsimulateddischarge[idx - 1]
        log.loggedsimulateddischarge[0] = simulateddischarge


class Set_ObservedDischarge_V1(modeltools.Method):
    """Append the given observed discharge value to the internal log of observed
    discharge by shifting the previously buffered values one position to the right
    and storing the new value at position 0.

    The given value may be |numpy.nan| when no observation is available.

    Example:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedobserveddischarge.shape = 3
        >>> logs.loggedobserveddischarge = 4.0, 3.0, 2.0
        >>> from numpy import nan
        >>> model.set_observeddischarge_v1(nan)
        >>> logs.loggedobserveddischarge
        loggedobserveddischarge(nan, 4.0, 3.0)
    """

    DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)
    UPDATEDSEQUENCES = (statcorr_logs.LoggedObservedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model, observeddischarge: float, /) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedobserveddischarge[idx] = log.loggedobserveddischarge[idx - 1]
        log.loggedobserveddischarge[0] = observeddischarge


class Calc_AveragedResidual_V1(modeltools.Method):
    r"""Determine the mean-value-based ARIMA residual once, at the first
    forecast step, and freeze it for the remainder of the current forecast
    horizon.

    |Calc_AveragedResidual_V1| averages the |LoggedObservedDischarge| and
    |LoggedSimulatedDischarge| entries covering the |ResidualAveragingWindow|
    log positions immediately preceding the current forecast run (log
    position ``0`` already holds the current forecast step's own values, so
    averaging starts at position ``1``) and stores their difference in
    |AveragedResidual|.  It leaves |AveragedResidual| unchanged whenever
    `forecast_step` is not zero (i.e., beyond the first forecast step) or
    |ResidualAveragingWindow| is zero (mean-value-based correction disabled).
    When the averaging window contains a |numpy.nan| value, it falls back to
    the given `fallback` residual instead (usually the pointwise residual
    already determined by |Determine_OutputCorrection_V1|).

    Examples:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> control.residualaveragingwindow(2)
        >>> derived.nmblogentries(3)
        >>> logs.loggedsimulateddischarge.shape = 3
        >>> logs.loggedobserveddischarge.shape = 3
        >>> logs.loggedsimulateddischarge = 3.0, 2.0, 4.0
        >>> logs.loggedobserveddischarge = nan, 3.0, 5.0

        On the first forecast step (`forecast_step` is ``0.0``), the average
        is taken from log positions ``1`` and ``2`` (mean observed ``4.0``,
        mean simulated ``3.0``):

        >>> from numpy import nan
        >>> model.calc_averagedresidual_v1(0.0, -9.0)
        >>> states.averagedresidual
        averagedresidual(1.0)

        On any later forecast step, the previously determined value remains
        unchanged, regardless of the current log contents:

        >>> logs.loggedsimulateddischarge = 3.0, 20.0, 40.0
        >>> logs.loggedobserveddischarge = nan, 30.0, 50.0
        >>> model.calc_averagedresidual_v1(1.0, -9.0)
        >>> states.averagedresidual
        averagedresidual(1.0)

        Setting |ResidualAveragingWindow| to zero disables mean-value-based
        correction; |Calc_AveragedResidual_V1| leaves |AveragedResidual|
        unchanged even on the first forecast step:

        >>> control.residualaveragingwindow(0)
        >>> states.averagedresidual(-9.0)
        >>> model.calc_averagedresidual_v1(0.0, -9.0)
        >>> states.averagedresidual
        averagedresidual(-9.0)

        A |numpy.nan| value within the averaging window makes
        |Calc_AveragedResidual_V1| fall back to the given `fallback` value:

        >>> control.residualaveragingwindow(2)
        >>> logs.loggedobserveddischarge = nan, nan, 50.0
        >>> model.calc_averagedresidual_v1(0.0, -9.0)
        >>> states.averagedresidual
        averagedresidual(-9.0)
    """

    CONTROLPARAMETERS = (statcorr_control.ResidualAveragingWindow,)
    DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        statcorr_logs.LoggedSimulatedDischarge,
        statcorr_logs.LoggedObservedDischarge,
    )
    UPDATEDSEQUENCES = (statcorr_states.AveragedResidual,)

    @staticmethod
    def __call__(
        model: modeltools.Model, forecast_step: float, fallback: float, /
    ) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess

        nmb = min(con.residualaveragingwindow, der.nmblogentries - 1)
        if forecast_step != 0.0 or nmb <= 0:
            return

        sum_obs: float = 0.0
        sum_sim: float = 0.0
        has_nan = False
        for idx in range(1, nmb + 1):
            obs_value: float = log.loggedobserveddischarge[idx]
            sim_value: float = log.loggedsimulateddischarge[idx]
            if modelutils.isnan(obs_value) or modelutils.isnan(sim_value):
                has_nan = True
                break
            sum_obs = sum_obs + obs_value
            sum_sim = sum_sim + sim_value
        sta.averagedresidual = fallback if has_nan else (sum_obs - sum_sim) / nmb


class Determine_OutputCorrection_V1(modeltools.Method):
    r"""Calculate the corrected discharge using an ARIMA(0,1,0) — random-walk —
    error model.

    The correction is derived from the most recently available residual
    (observed minus simulated discharge).  The "most recent" residual is taken
    from the latest log entry where the observed discharge is not |numpy.nan|,
    searching back at most |MaxResidualLookback| log entries (or the entire
    log, whichever is smaller).  When no observation is available within that
    range, the corrected discharge equals the current simulated discharge.

    How that residual is applied to the current simulated ("forecast")
    discharge depends on how the latter (:math:`sim_0`) compares to the
    simulated discharge at the time the residual was determined (:math:`sim_k`,
    with :math:`k` denoting the most recent log index for which :math:`obs_k
    \neq \mathrm{nan}`, and :math:`f_{red}` denoting |ReductionFactor|):

    * If :math:`sim_0 > sim_k` (and :math:`sim_k > 0`),
      |Determine_OutputCorrection_V1| shifts :math:`sim_0` *additively* by the
      |ReductionFactor|-damped residual, capped at |MaxAbsoluteShift| (in
      m³/s):

        :math:`q_{corr} = sim_0 + \mathrm{clip}\left((obs_k - sim_k) \cdot
        f_{red},\ \pm MaxAbsoluteShift\right)`

    * Otherwise (including :math:`sim_k \leq 0`, for which a relative shift
      would be undefined), it shifts :math:`sim_0` *multiplicatively* instead,
      expressing the damped residual as a percentage of :math:`sim_k` and
      capping that percentage at |MaxRelativeShift|:

        :math:`q_{corr} = sim_0 \cdot \left(1 + \mathrm{clip}\left((obs_k -
        sim_k) \cdot f_{red} / sim_k,\ \pm MaxRelativeShift / 100\right)
        \right)`

      Applying the residual as a percentage rather than a constant offset
      keeps the correction from overshooting or turning negative while the
      forecasted discharge recedes towards zero.

    The residual (:math:`obs_k - sim_k` above) used in either branch is not
    necessarily the pointwise one.  Setting |ResidualAveragingWindow| to a
    value greater than zero switches to a mean-value-based residual instead —
    the difference between the mean observed and the mean simulated discharge
    over that many log entries immediately preceding the current forecast run
    (determined once, at the first forecast step, via
    |Calc_AveragedResidual_V1|, and frozen in |AveragedResidual| for the
    remainder of the forecast horizon).  Since that mean-value-based residual
    generally does not equal the pointwise residual at the forecast's start,
    switching to it abruptly would cause a jump in the corrected discharge
    right where the forecast begins.  To avoid this, |Determine_OutputCorrection_V1|
    starts every forecast run with the pointwise residual (so the corrected
    discharge picks up smoothly where the last measurement left off) and then
    linearly blends it towards the mean-value-based residual over
    |ResidualTransitionTime| forecast steps, applying the mean-value-based
    residual unabated from then on.  Setting |ResidualAveragingWindow| to zero
    (the default behaviour before mean-value-based correction was introduced)
    disables this mechanism entirely, relying on the pointwise residual alone,
    as described above.

    Within the NQ and MQ ranges, |Determine_OutputCorrection_V1| additionally
    assesses whether the measured discharge behaves in a stationary way.  It
    takes the quotient of the minimum and the maximum |LoggedObservedDischarge|
    value within the most recent |NqmStationarityWindow| log entries.  Whenever
    this quotient falls below |QminQmax| (given in %), it considers the flow
    conditions instationary and linearly reduces |ReductionFactor| (the factor
    :math:`f_{red}` in the equation above) towards zero, taking as many steps as
    given by the NQ or MQ entry of |LinearReductionTime| (depending on the
    current flow range).  As soon as the quotient reaches |QminQmax| again (or a
    |numpy.nan| value prevents its calculation), |ReductionFactor| jumps back to
    ``1.0``, applying the correction unabated again.  |ReductionFactor| also
    resets to ``1.0`` whenever the current flow condition falls into the HQ
    range, for which this stationarity check is not defined.

    |Determine_OutputCorrection_V1| only *reassesses* stationarity (the
    quotient-based check described above) and the NQ/MQ/HQ flow condition
    while |Options.simulationmode| equals `historical`, remembering their
    outcomes in |Stationary| and |FlowCondition|, respectively.  While
    |Options.simulationmode| equals `forecast`, it reuses both values from the
    most recent `historical` assessment instead of recomputing them —
    recomputing would be unreliable anyway, since |LoggedObservedDischarge|
    keeps receiving |numpy.nan| values throughout the forecast (see
    |Calc_OutputCorr_V1|), which the quotient-based check always interprets as
    "stationary", and since the currently simulated discharge could
    temporarily cross into the HQ range and mask an instationary NQ/MQ
    situation identified right before the forecast started.  So, once a
    `historical` run has flagged conditions as instationary in the NQ or MQ
    range, |ReductionFactor| keeps ramping towards zero (or staying at
    ``0.0``) for the entire forecast horizon, regardless of how the actually
    simulated discharge subsequently develops, instead of jumping back to
    ``1.0`` either as soon as the last real observation drops out of the
    logging window or whenever the forecasted discharge happens to pass
    through the HQ range.

    Examples:

        Three log entries are available, the most recent observation (at
        position 0) is non-|numpy.nan|, so the correction reproduces the current
        observation.  The measured discharge is perfectly stationary (the
        quotient of its minimum and maximum equals |QminQmax|), so
        |ReductionFactor| remains at its initial value of ``1.0``:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> control.evaluationwindow(3)
        >>> control.corrnq(True)
        >>> control.corrmq(True)
        >>> control.corrhq(True)
        >>> control.limitnqm(3.0)
        >>> control.limitmqh(5.0)
        >>> control.qminqmax(50.0)
        >>> control.nqmstationaritywindow(3)
        >>> control.linearreductiontime(2, 2)
        >>> control.maxresiduallookback(3)
        >>> control.maxabsoluteshift(100.0)
        >>> control.maxrelativeshift(1000.0)
        >>> control.residualaveragingwindow(0)
        >>> control.residualtransitiontime(0)
        >>> states.reductionfactor(1.0)
        >>> states.stationary(1.0)
        >>> logs.loggedsimulateddischarge.shape = 3
        >>> logs.loggedobserveddischarge.shape = 3
        >>> logs.loggedsimulateddischarge = 5.0, 3.0, 2.0
        >>> logs.loggedobserveddischarge = 6.0, 4.0, 3.0
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(6.0)
        >>> states.reductionfactor
        reductionfactor(1.0)

        Disabling correction for the MQ range returns the uncorrected simulated value:

        >>> control.corrmq(False)
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(5.0)

        Simulated discharges averaging 1.5 m³/s place the model in the NQ range.
        With NQ correction enabled, the residual (2.0 − 1.0 = 1.0) is applied:

        >>> logs.loggedsimulateddischarge = 1.0, 2.0, 1.5
        >>> logs.loggedobserveddischarge = 2.0, 3.0, 2.5
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(2.0)

        The two most recent observations are missing, so the residual is taken
        from the third log entry and added to the current simulated discharge.
        Missing observations also make it impossible to assess stationarity, so
        |Determine_OutputCorrection_V1| assumes stationary conditions and leaves
        |ReductionFactor| untouched:

        >>> from numpy import nan
        >>> control.corrmq(True)
        >>> logs.loggedsimulateddischarge = 5.0, 3.0, 2.0
        >>> logs.loggedobserveddischarge = nan, nan, 3.0
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(6.0)

        All observations are missing — no correction is applied:

        >>> logs.loggedobserveddischarge = nan, nan, nan
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(5.0)

        Sustained instationary conditions in the NQ range (the quotient of the
        minimum and the maximum observed discharge, ``0.5 / 5.0 = 10 %``, falls
        well below |QminQmax|) linearly reduce |ReductionFactor| to zero within
        the two steps given by the NQ entry of |LinearReductionTime|:

        >>> logs.loggedsimulateddischarge = 1.0, 1.0, 1.0
        >>> logs.loggedobserveddischarge = 0.5, 5.0, 5.0
        >>> model.determine_outputcorrection_v1(False)
        >>> states.reductionfactor
        reductionfactor(0.5)
        >>> fluxes.correctedq
        correctedq(0.75)

        >>> model.determine_outputcorrection_v1(False)
        >>> states.reductionfactor
        reductionfactor(0.0)
        >>> fluxes.correctedq
        correctedq(1.0)

        The stationarity check does not apply to the HQ range, so switching to
        high flow conditions resets |ReductionFactor| to ``1.0`` regardless of
        the (still instationary) measured discharge:

        >>> logs.loggedsimulateddischarge = 6.0, 6.0, 6.0
        >>> logs.loggedobserveddischarge = 7.0, 5.0, 5.0
        >>> model.determine_outputcorrection_v1(False)
        >>> states.reductionfactor
        reductionfactor(1.0)
        >>> fluxes.correctedq
        correctedq(7.0)

        Once the measured discharge becomes stationary again (quotient
        ``4.0 / 5.0 = 80 %``, at or above |QminQmax|), |ReductionFactor| jumps
        back to ``1.0`` immediately, applying the correction unabated:

        >>> logs.loggedsimulateddischarge = 1.0, 1.0, 1.0
        >>> logs.loggedobserveddischarge = 4.0, 5.0, 5.0
        >>> model.determine_outputcorrection_v1(False)
        >>> states.reductionfactor
        reductionfactor(1.0)
        >>> fluxes.correctedq
        correctedq(4.0)

        Setting the NQ entry of |LinearReductionTime| to zero reduces
        |ReductionFactor| to zero immediately once instationary conditions occur:

        >>> control.linearreductiontime(0, 2)
        >>> logs.loggedobserveddischarge = 0.5, 5.0, 5.0
        >>> model.determine_outputcorrection_v1(False)
        >>> states.reductionfactor
        reductionfactor(0.0)
        >>> fluxes.correctedq
        correctedq(1.0)

        Instationary conditions detected during `historical` mode (the second
        call argument is |False|) start a ramp towards zero (here, with
        |LinearReductionTime| reset to two steps):

        >>> control.linearreductiontime(2, 2)
        >>> states.reductionfactor(1.0)
        >>> logs.loggedsimulateddischarge = 1.0, 1.0, 1.0
        >>> logs.loggedobserveddischarge = 0.5, 5.0, 5.0
        >>> model.determine_outputcorrection_v1(False)
        >>> states.stationary
        stationary(0.0)
        >>> states.reductionfactor
        reductionfactor(0.5)

        Switching to `forecast` mode (the second call argument is now |True|,
        as |Calc_OutputCorr_V1| does automatically) and feeding |numpy.nan|
        observations does not reassess |Stationary|; the ramp initiated above
        simply continues:

        >>> logs.loggedsimulateddischarge = 1.0, 1.0, 1.0
        >>> logs.loggedobserveddischarge = nan, nan, nan
        >>> model.determine_outputcorrection_v1(True)
        >>> states.stationary
        stationary(0.0)
        >>> states.reductionfactor
        reductionfactor(0.0)
        >>> fluxes.correctedq
        correctedq(1.0)

        A further forecast step confirms |ReductionFactor| stays at ``0.0``
        instead of jumping back to ``1.0``, as it would if |Stationary| were
        reassessed using the now entirely |numpy.nan| logging window:

        >>> model.determine_outputcorrection_v1(True)
        >>> states.reductionfactor
        reductionfactor(0.0)
        >>> fluxes.correctedq
        correctedq(1.0)

        Not only |Stationary| but also the flow condition itself (NQ, MQ, or
        HQ, persisted in |FlowCondition|) is frozen at its most recent
        `historical` assessment (here, NQ) and is not reassessed while
        forecasting.  So even though the currently simulated discharge would
        classify as HQ now (which used to reset |ReductionFactor| to ``1.0``
        immediately, since the stationarity check does not apply to the HQ
        range), the frozen NQ classification keeps applying, and the ramp
        (already at its floor of ``0.0``) is left untouched:

        >>> logs.loggedsimulateddischarge = 10.0, 10.0, 10.0
        >>> logs.loggedobserveddischarge = nan, nan, nan
        >>> model.determine_outputcorrection_v1(True)
        >>> states.flowcondition
        flowcondition(0.0)
        >>> states.reductionfactor
        reductionfactor(0.0)
        >>> fluxes.correctedq
        correctedq(10.0)

        Enlarging the log beyond |EvaluationWindow| does not change the flow
        condition classification, which always relies on the *most recently*
        logged |LoggedSimulatedDischarge| entries (index ``0`` upwards) and
        never on the oldest ones sitting near the end of a larger log (which
        can well still be |numpy.nan|, as is the case for the newly added
        entries here):

        >>> control.linearreductiontime(2, 2)
        >>> states.reductionfactor(1.0)
        >>> derived.nmblogentries(5)
        >>> logs.loggedsimulateddischarge.shape = 5
        >>> logs.loggedobserveddischarge.shape = 5
        >>> logs.loggedsimulateddischarge = 1.0, 1.0, 1.0, nan, nan
        >>> logs.loggedobserveddischarge = 0.5, 5.0, 5.0, nan, nan
        >>> model.determine_outputcorrection_v1(False)
        >>> states.stationary
        stationary(0.0)
        >>> states.reductionfactor
        reductionfactor(0.5)

        Restricting |MaxResidualLookback| to fewer entries than the full log
        makes |Determine_OutputCorrection_V1| stop searching for a valid
        residual once that limit is reached, applying no correction even
        though an older, still-logged observation would otherwise be usable:

        >>> control.maxresiduallookback(2)
        >>> logs.loggedsimulateddischarge = 1.0, 1.0, 1.0, nan, nan
        >>> logs.loggedobserveddischarge = nan, nan, 3.0, nan, nan
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(1.0)

        Enlarging |MaxResidualLookback| to reach that entry again reinstates
        the correction:

        >>> control.maxresiduallookback(3)
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(3.0)

        So far, the current forecast value (log position 0) has always been
        at or above the simulated discharge at the time the residual was
        determined, so all examples above used the additive (or, at position
        0 itself, an equivalent) shift.  Resetting the log to a *receding*
        forecast — position 0 has already dropped clearly below the value at
        the residual's log position — switches to the relative (percentage)
        shift instead:

        >>> logs.loggedsimulateddischarge = 2.0, 10.0, 10.0, nan, nan
        >>> logs.loggedobserveddischarge = nan, 12.0, nan, nan, nan
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(2.4)

        Limiting |MaxRelativeShift| caps that percentage before it is
        converted back into an absolute shift:

        >>> control.maxrelativeshift(10.0)
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(2.2)

        Likewise, |MaxAbsoluteShift| caps the additive shift applied whenever
        the forecast value exceeds the anchor value:

        >>> control.maxabsoluteshift(1.0)
        >>> logs.loggedsimulateddischarge = 12.0, 10.0, 10.0, nan, nan
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(13.0)

        When the anchor value is zero or negative, a relative shift would be
        undefined (division by zero), so |Determine_OutputCorrection_V1|
        falls back to the additive shift in that case as well, even though
        the forecast value does not exceed the anchor value:

        >>> control.maxabsoluteshift(100.0)
        >>> logs.loggedsimulateddischarge = 0.0, 0.0, 10.0, nan, nan
        >>> logs.loggedobserveddischarge = nan, 2.0, nan, nan, nan
        >>> model.determine_outputcorrection_v1(False)
        >>> fluxes.correctedq
        correctedq(2.0)

        Setting |ResidualAveragingWindow| to a value greater than zero
        switches to the mean-value-based residual, blended in linearly over
        |ResidualTransitionTime| forecast steps.  We reset the log to a
        short, clean example (four entries) and freeze |FlowCondition| and
        |Stationary| directly (instead of deriving them from a preceding
        `historical` call) to keep the focus on the transition mechanism:

        >>> control.maxresiduallookback(4)
        >>> control.maxabsoluteshift(100.0)
        >>> control.maxrelativeshift(1000.0)
        >>> control.residualaveragingwindow(2)
        >>> control.residualtransitiontime(2)
        >>> derived.nmblogentries(4)
        >>> logs.loggedsimulateddischarge.shape = 4
        >>> logs.loggedobserveddischarge.shape = 4
        >>> states.flowcondition(0.0)
        >>> states.stationary(1.0)
        >>> states.reductionfactor(1.0)
        >>> states.forecaststep(0.0)

        The most recent (pointwise) residual, taken from log position ``1``
        (``9.0 - 8.0 = 1.0``), differs from the mean-value-based residual
        taken from log positions ``1`` and ``2`` (mean observed ``8.5``, mean
        simulated ``6.0``, hence ``2.5``).  On the first forecast step,
        |Determine_OutputCorrection_V1| applies the pointwise residual
        unabated:

        >>> logs.loggedsimulateddischarge = 10.0, 8.0, 4.0, nan
        >>> logs.loggedobserveddischarge = nan, 9.0, 8.0, nan
        >>> model.determine_outputcorrection_v1(True)
        >>> states.averagedresidual
        averagedresidual(2.5)
        >>> fluxes.correctedq
        correctedq(11.0)

        Halfway through the two-step transition, the applied residual is the
        average of both (``1.75``):

        >>> logs.loggedsimulateddischarge = 11.0, 10.0, 8.0, 4.0
        >>> logs.loggedobserveddischarge = nan, nan, 9.0, 8.0
        >>> model.determine_outputcorrection_v1(True)
        >>> fluxes.correctedq
        correctedq(12.75)

        Once the transition period has elapsed, the full mean-value-based
        residual applies, regardless of the (still aging) pointwise residual:

        >>> logs.loggedsimulateddischarge = 12.0, 11.0, 10.0, 8.0
        >>> logs.loggedobserveddischarge = nan, nan, nan, 9.0
        >>> model.determine_outputcorrection_v1(True)
        >>> states.averagedresidual
        averagedresidual(2.5)
        >>> fluxes.correctedq
        correctedq(14.5)
    """

    SUBMETHODS = (Calc_AveragedResidual_V1,)
    CONTROLPARAMETERS = (
        statcorr_control.CorrNQ,
        statcorr_control.CorrMQ,
        statcorr_control.CorrHQ,
        statcorr_control.LimitNQM,
        statcorr_control.LimitMQH,
        statcorr_control.EvaluationWindow,
        statcorr_control.MaxResidualLookback,
        statcorr_control.MaxAbsoluteShift,
        statcorr_control.MaxRelativeShift,
        statcorr_control.ResidualAveragingWindow,
        statcorr_control.ResidualTransitionTime,
        statcorr_control.QminQmax,
        statcorr_control.NqmStationarityWindow,
        statcorr_control.LinearReductionTime,
    )
    DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        statcorr_logs.LoggedSimulatedDischarge,
        statcorr_logs.LoggedObservedDischarge,
    )
    UPDATEDSEQUENCES = (
        statcorr_states.ReductionFactor,
        statcorr_states.Stationary,
        statcorr_states.FlowCondition,
        statcorr_states.ForecastStep,
        statcorr_states.AveragedResidual,
    )
    RESULTSEQUENCES = (statcorr_fluxes.CorrectedQ,)

    @staticmethod
    def __call__(model: modeltools.Model, isforecastmode: bool, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess

        assert der.nmblogentries >= con.evaluationwindow

        flow_condition: int
        if isforecastmode:
            flow_condition = int(sta.flowcondition)
        else:
            mean_simulated: float = 0.0
            for idx in range(con.evaluationwindow):
                mean_simulated = mean_simulated + log.loggedsimulateddischarge[idx]
            mean_simulated = mean_simulated / con.evaluationwindow

            if mean_simulated < con.limitnqm:
                flow_condition = 0
            elif mean_simulated < con.limitmqh:
                flow_condition = 1
            else:
                flow_condition = 2
            sta.flowcondition = float(flow_condition)

        if (
            (flow_condition == 0 and con.corrnq is False)
            or (flow_condition == 1 and con.corrmq is False)
            or (flow_condition == 2 and con.corrhq is False)
        ):
            flu.correctedq = log.loggedsimulateddischarge[0]
            return

        residual: float = 0.0
        sim_anchor: float = 0.0
        for idx in range(min(der.nmblogentries, con.maxresiduallookback)):
            if not modelutils.isnan(log.loggedobserveddischarge[idx]):
                sim_anchor = log.loggedsimulateddischarge[idx]
                residual = log.loggedobserveddischarge[idx] - sim_anchor
                break

        if flow_condition == 2:
            sta.reductionfactor = 1.0
        else:
            if not isforecastmode:
                nmb = min(der.nmblogentries, con.nqmstationaritywindow)
                stationary: bool = True
                has_nan = False
                qmin: float = modelutils.inf
                qmax: float = -modelutils.inf
                for idx in range(nmb):
                    value: float = log.loggedobserveddischarge[idx]
                    if modelutils.isnan(value):
                        has_nan = True
                        break
                    qmin = min(qmin, value)
                    qmax = max(qmax, value)
                if not has_nan and qmax > 0.0:
                    stationary = (qmin / qmax) * 100.0 >= con.qminqmax
                sta.stationary = 1.0 if stationary else 0.0

            if sta.stationary:
                sta.reductionfactor = 1.0
            else:
                idx_regime = 0 if flow_condition == 0 else 1
                reductiontime = con.linearreductiontime[idx_regime]
                if reductiontime <= 0:
                    sta.reductionfactor = 0.0
                else:
                    sta.reductionfactor = max(
                        0.0, sta.reductionfactor - 1.0 / reductiontime
                    )

        forecast_step: float = sta.forecaststep if isforecastmode else 0.0
        sta.forecaststep = (forecast_step + 1.0) if isforecastmode else 0.0
        model.calc_averagedresidual_v1(forecast_step, residual)
        effective_residual: float = (
            residual
            if con.residualaveragingwindow <= 0
            else residual
            + (
                1.0
                if con.residualtransitiontime <= 0
                else min(1.0, forecast_step / con.residualtransitiontime)
            )
            * (sta.averagedresidual - residual)
        )

        forecast_value: float = log.loggedsimulateddischarge[0]
        damped_residual: float = effective_residual * sta.reductionfactor
        max_fraction: float = con.maxrelativeshift / 100.0
        shift: float = (
            forecast_value
            * min(max_fraction, max(-max_fraction, damped_residual / sim_anchor))
            if sim_anchor > 0.0 and forecast_value <= sim_anchor
            else min(con.maxabsoluteshift, max(-con.maxabsoluteshift, damped_residual))
        )
        flu.correctedq = forecast_value + shift


class Get_CorrectedOutput_V1(modeltools.Method):
    """Return the most recently calculated corrected discharge in m³/s.

    Example:

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> fluxes.correctedq = 2.5
        >>> from hydpy import round_
        >>> round_(model.get_correctedoutput_v1())
        2.5
    """

    REQUIREDSEQUENCES = (statcorr_fluxes.CorrectedQ,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> float:
        flu = model.sequences.fluxes.fastaccess
        return flu.correctedq


class Sub_OutputCorrModel(modeltools.AdHocModel):
    """Base class for submodels that comply with the submodel interfaces defined in
    module |statcorrinterfaces|."""
