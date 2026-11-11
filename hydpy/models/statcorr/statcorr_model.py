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


class Pick_OriginalQ_V1(modeltools.Method):
    r"""Sum up the original discharge from all inlet nodes.

    Basic equation:
      :math:`OriginalQ = \sum Q`

    Example:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> inlets.q.shape = 2
        >>> inlets.q = 2.0, 4.0
        >>> model.pick_originalq_v1()
        >>> fluxes.originalq
        originalq(6.0)
    """

    REQUIREDSEQUENCES = (statcorr_inlets.Q,)
    RESULTSEQUENCES = (statcorr_fluxes.OriginalQ,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.originalq = 0.0
        for idx in range(inl.len_q):
            flu.originalq += inl.q[idx]


class Calc_OutputCorr_OutputCorrModel_V1(modeltools.Method):
    """Let a submodel that complies with the |OutputCorrModel_V1| interface correct
    the current simulated discharge and take over its result if it is active.

    See |Calc_OutputCorr_V1| for examples.
    """

    SUBMODELINTERFACES = (statcorrinterfaces.OutputCorrModel_V1,)
    REQUIREDSEQUENCES = (statcorr_fluxes.OriginalQ, statcorr_inputs.Discharge)
    RESULTSEQUENCES = (statcorr_fluxes.CorrectedQ,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: statcorrinterfaces.OutputCorrModel_V1, /
    ) -> None:
        flu = model.sequences.fluxes.fastaccess
        inp = model.sequences.inputs.fastaccess
        submodel.set_simulatedvalue(flu.originalq)
        if model.runsettings.simulationmode == modelutils.FORECAST:
            submodel.set_observedvalue(modelutils.nan)
        else:
            submodel.set_observedvalue(inp.discharge)
        submodel.determine_outputcorrection()
        if submodel.is_active():
            flu.correctedq = submodel.get_correctedoutput()


class Calc_OutputCorr_V1(modeltools.Method):
    """Apply each |OutputCorrModel_V1| submodel to the current simulated and observed
    discharge and combine their results into the corrected discharge.

    This method orchestrates one or more submodels of identical interface type:

      1. The current simulated discharge (|OriginalQ|) and observed discharge
         (|Discharge|) are passed to each attached |OutputCorrModel_V1| submodel
         via |OutputCorrModel_V1.set_simulatedvalue| and
         |OutputCorrModel_V1.set_observedvalue|.  While |Options.simulationmode|
         equals `forecast`, |Calc_OutputCorr_V1| passes |numpy.nan| instead of the
         actual value of |Discharge|, regardless of whether an observation is
         available.  This relies on the assumption that a previous `historical`
         simulation run already logged all relevant past observations and
         simulations (read in as conditions).
      2. Each submodel computes its corrected discharge via
         |OutputCorrModel_V1.determine_outputcorrection|.
      3. Each submodel decides for itself, based on its own |Active| flag, its
         |CorrectionMode|, and its |LowerLimit| and |UpperLimit| parameters,
         whether it is responsible for the current observed discharge (see
         |EvaluatedValue| and |OutputCorrModel_V1.is_active|).  The corrected
         output of the *last* responsible submodel is taken as |CorrectedQ|.  When
         no submodel is attached or responsible, |CorrectedQ| equals |OriginalQ|.
         Hence, attaching several submodels configured for mutually exclusive
         discharge ranges lets only the one responsible for the current observed
         discharge take effect.

    Examples:

        Without any attached submodel, the corrected discharge equals the original
        discharge:

        >>> from hydpy.models.statcorr_main import *
        >>> parameterstep()
        >>> fluxes.originalq = 2.0
        >>> inputs.discharge = 3.0
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(2.0)

        With a single attached |statcorr_arima010| submodel, the corrected
        discharge is the original discharge plus the most recent residual (here:
        ``3.0 - 2.0 = 1.0``, applied to the new original discharge ``2.5``).  By
        default, we make the submodel responsible for all discharges and disable
        the stationarity check so that it never suppresses the correction:

        >>> from numpy import inf
        >>> def configure(submodel, lowerlimit=0.0, upperlimit=inf):
        ...     submodel.parameters.control.active(True)
        ...     submodel.parameters.control.correctionmode(option="both")
        ...     submodel.parameters.control.lowerlimit(lowerlimit)
        ...     submodel.parameters.control.upperlimit(upperlimit)
        ...     submodel.parameters.control.evaluationwindow(1)
        ...     submodel.parameters.control.maxnanskip(2)
        ...     submodel.parameters.control.maxabsshift(100.0)
        ...     submodel.parameters.control.maxrelshift(10.0)
        ...     submodel.parameters.control.averagingwindow(0)
        ...     submodel.parameters.control.transitionsteps(0)
        ...     submodel.parameters.control.stationaritycheck(active=False)
        ...     submodel.parameters.control.reductionsteps(1)

        >>> nmbsubmodels(1)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=0
        ... ) as submodel:
        ...     configure(submodel)
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(3.0)
        >>> from numpy import nan
        >>> fluxes.originalq = 2.5
        >>> inputs.discharge = nan
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(3.5)

        We now attach two submodels responsible for different discharge ranges.
        The first one covers discharges below 3 m³/s, the second one all
        discharges from 3 m³/s upwards:

        >>> nmbsubmodels(2)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=0
        ... ) as submodel:
        ...     configure(submodel, upperlimit=3.0)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=1
        ... ) as submodel:
        ...     configure(submodel, lowerlimit=3.0)

        The submodels decide based on the observed discharge.  For an observed
        discharge of 2.5 m³/s, only the first submodel is responsible, although the
        original discharge of 3.5 m³/s lies within the range of the second one.
        Hence, the corrected output of the first submodel wins, although the second
        submodel comes later and returns the original discharge:

        >>> fluxes.originalq = 3.5
        >>> inputs.discharge = 2.5
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(2.5)
        >>> model.outputcorrmodels[0].sequences.fluxes.isactive
        isactive(1.0)
        >>> model.outputcorrmodels[1].sequences.fluxes.isactive
        isactive(0.0)

        For an observed discharge of 4.0 m³/s, the second submodel takes over:

        >>> fluxes.originalq = 2.5
        >>> inputs.discharge = 4.0
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(4.0)
        >>> model.outputcorrmodels[0].sequences.fluxes.isactive
        isactive(0.0)
        >>> model.outputcorrmodels[1].sequences.fluxes.isactive
        isactive(1.0)

        If no submodel is responsible, |CorrectedQ| equals |OriginalQ|:

        >>> model.outputcorrmodels[1].parameters.control.active(False)
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(2.5)

        While |Options.simulationmode| equals ``forecast``, |Calc_OutputCorr_V1|
        ignores the actual value of |Discharge| and passes |numpy.nan| to the
        submodels instead, relying on their logic to
        keep applying the most recently logged residual (see |statcorr_arima010|
        for the mechanism and the module docstring of |statcorr_main| for the
        assumed workflow of a preceding `historical` run).  The main model and
        its submodels read the current simulation mode at runtime via
        |Model.runsettings|, so changing |Options.simulationmode| takes effect
        immediately without updating any parameters:

        >>> nmbsubmodels(1)
        >>> with model.add_outputcorrmodel_v1(
        ...     "statcorr_arima010", position=0
        ... ) as submodel:
        ...     configure(submodel)
        >>> model.parameters.update()

        Two `historical` steps establish a residual of ``0.5``:

        >>> fluxes.originalq = 1.0
        >>> inputs.discharge = 1.5
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(1.5)
        >>> fluxes.originalq = 2.0
        >>> inputs.discharge = 2.5
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(2.5)

        Switching to `forecast` mode and feeding an implausible |Discharge|
        value (``999.0``, which would dominate the result if it were not
        ignored) still reproduces the persisted residual of ``0.5``:

        >>> from hydpy import pub
        >>> with pub.options.simulationmode("forecast"):
        ...     fluxes.originalq = 3.0
        ...     inputs.discharge = 999.0
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(3.5)
        >>> with pub.options.simulationmode("forecast"):
        ...     fluxes.originalq = 4.0
        ...     inputs.discharge = 999.0
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(4.5)

        Even once the last real observation drops out of the submodel's log
        (the current entry plus the two preceding ones due to |MaxNaNSkip|), the
        persisted residual keeps applying without limit -- only |ReductionFactor|
        (via |StationarityCheck| and |ReductionSteps|, disabled here) could still
        fade it out:

        >>> with pub.options.simulationmode("forecast"):
        ...     fluxes.originalq = 5.0
        ...     inputs.discharge = 999.0
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(5.5)
        >>> with pub.options.simulationmode("forecast"):
        ...     fluxes.originalq = 6.0
        ...     inputs.discharge = 999.0
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(6.5)
    """

    SUBMODELINTERFACES = (statcorrinterfaces.OutputCorrModel_V1,)
    SUBMETHODS = (Calc_OutputCorr_OutputCorrModel_V1,)
    CONTROLPARAMETERS = (statcorr_control.NmbSubmodels,)
    REQUIREDSEQUENCES = (statcorr_fluxes.OriginalQ, statcorr_inputs.Discharge)
    RESULTSEQUENCES = (statcorr_fluxes.CorrectedQ,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        flu = model.sequences.fluxes.fastaccess
        con = model.parameters.control.fastaccess
        flu.correctedq = flu.originalq
        for i in range(con.nmbsubmodels):
            if model.outputcorrmodels.typeids[i] == 1:
                model.calc_outputcorr_outputcorrmodel_v1(
                    cast(
                        statcorrinterfaces.OutputCorrModel_V1,
                        model.outputcorrmodels.submodels[i],
                    )
                )


class Pass_CorrectedQ_V1(modeltools.Method):
    """Pass the corrected discharge on to the outlet link sequence, unless
    |Propagate| is |False|, in which case the original discharge is
    passed on instead.  Either way, |CorrectedQ| remains available for local
    output at the current gauge.

    Basic equation:
        :math:`Q_{outlets} = CorrectedQ` (if |Propagate|) or
        :math:`Q_{outlets} = OriginalQ` (otherwise)

    Examples:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> fluxes.originalq = 1.0
        >>> fluxes.correctedq = 2.0

        >>> propagate(True)
        >>> model.pass_correctedq_v1()
        >>> outlets.q
        q(2.0)

        >>> propagate(False)
        >>> model.pass_correctedq_v1()
        >>> outlets.q
        q(1.0)
    """

    CONTROLPARAMETERS = (statcorr_control.Propagate,)
    REQUIREDSEQUENCES = (statcorr_fluxes.OriginalQ, statcorr_fluxes.CorrectedQ)
    RESULTSEQUENCES = (statcorr_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q = flu.correctedq if con.propagate else flu.originalq


class Set_SimulatedValue_V1(modeltools.Method):
    """Append the given simulated value to the internal log of simulated values
    by shifting the previously buffered values one position to the right
    and storing the new value at position 0.

    Example:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedsimulation = 4.0, 3.0, 2.0
        >>> model.set_simulatedvalue_v1(5.0)
        >>> logs.loggedsimulation
        loggedsimulation(5.0, 4.0, 3.0)
    """

    DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)
    UPDATEDSEQUENCES = (statcorr_logs.LoggedSimulation,)

    @staticmethod
    def __call__(model: modeltools.Model, simulatedvalue: float, /) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedsimulation[idx] = log.loggedsimulation[idx - 1]
        log.loggedsimulation[0] = simulatedvalue


class Set_ObservedValue_V1(modeltools.Method):
    """Append the given observed value to the internal log of observed values
    by shifting the previously buffered values one position to the right
    and storing the new value at position 0.

    The given value may be |numpy.nan| when no observation is available.

    Example:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedobservation = 4.0, 3.0, 2.0
        >>> from numpy import nan
        >>> model.set_observedvalue_v1(nan)
        >>> logs.loggedobservation
        loggedobservation(nan, 4.0, 3.0)
    """

    DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)
    UPDATEDSEQUENCES = (statcorr_logs.LoggedObservation,)

    @staticmethod
    def __call__(model: modeltools.Model, observedvalue: float, /) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedobservation[idx] = log.loggedobservation[idx - 1]
        log.loggedobservation[0] = observedvalue


class Calc_EvaluatedValue_V1(modeltools.Method):
    r"""Calculate the mean of the available (non-|numpy.nan|) values among the
    |EvaluationWindow| most recent |LoggedObservation| values while
    |Options.simulationmode| is `historical`.

    Basic equation:
      :math:`EvaluatedValue = \frac{1}{n}
      \sum_{i=0}^{EvaluationWindow-1} LoggedObservation_i`

    The sum covers only the available values, and :math:`n` is their number.  If all
    values are |numpy.nan|, |EvaluatedValue| keeps its previous value, so the
    responsible submodel (see |Calc_IsActive_V1|) does not change during gaps in the
    observations.

    While |Options.simulationmode| is `forecast`, |Calc_EvaluatedValue_V1| keeps the
    value of the most recent `historical` assessment, so the responsible submodel
    does not change throughout the forecast horizon.

    Examples:

        |Calc_EvaluatedValue_V1| always relies on the *most recently* logged values
        (index ``0`` upwards) and never on the oldest ones sitting near the end of a
        larger log:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import nan
        >>> control.evaluationwindow(3)
        >>> derived.nmblogentries(5)
        >>> logs.loggedobservation = 1.0, 2.0, 6.0, 8.0, 9.0
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> model.calc_evaluatedvalue_v1()
        >>> states.evaluatedvalue
        evaluatedvalue(3.0)

        Missing observations are left out:

        >>> logs.loggedobservation = 1.0, nan, 5.0, 8.0, 9.0
        >>> model.calc_evaluatedvalue_v1()
        >>> states.evaluatedvalue
        evaluatedvalue(3.0)

        If no observation is available, |EvaluatedValue| keeps its previous value:

        >>> logs.loggedobservation = nan, nan, nan, 8.0, 9.0
        >>> model.calc_evaluatedvalue_v1()
        >>> states.evaluatedvalue
        evaluatedvalue(3.0)

        In `forecast` mode, |EvaluatedValue| stays frozen:

        >>> pub.options.simulationmode = "forecast"
        >>> logs.loggedobservation = 10.0, 10.0, 10.0, nan, nan
        >>> model.calc_evaluatedvalue_v1()
        >>> states.evaluatedvalue
        evaluatedvalue(3.0)
        >>> del pub.options.simulationmode
    """

    CONTROLPARAMETERS = (statcorr_control.EvaluationWindow,)
    REQUIREDSEQUENCES = (statcorr_logs.LoggedObservation,)
    UPDATEDSEQUENCES = (statcorr_states.EvaluatedValue,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess
        if model.runsettings.simulationmode == modelutils.HISTORICAL:
            sum_observed: float = 0.0
            nmb_observed = 0
            for idx in range(con.evaluationwindow):
                if not modelutils.isnan(log.loggedobservation[idx]):
                    sum_observed = sum_observed + log.loggedobservation[idx]
                    nmb_observed = nmb_observed + 1
            if nmb_observed > 0:
                sta.evaluatedvalue = sum_observed / nmb_observed


class Calc_IsActive_V1(modeltools.Method):
    r"""Decide whether the submodel is responsible for correcting the current
    simulated value.

    Each submodel is responsible for a specific value range only.  It corrects the
    simulated values only while |Active| is |True|, |CorrectionMode| allows a
    correction in the current simulation mode (see |Options.simulationmode|), and
    |EvaluatedValue| (:math:`\overline{obs}`) lies within the range defined by
    |LowerLimit| and |UpperLimit|:

        :math:`LowerLimit \leq \overline{obs} < UpperLimit`

    As long as |EvaluatedValue| is |numpy.nan| (before the first observation is
    available), the submodel is not active.

    |Calc_IsActive_V1| checks this condition in each simulation step, so changes of
    |Active|, |CorrectionMode|, |LowerLimit|, or |UpperLimit| take effect
    immediately.

    Examples:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import inf
        >>> control.active(True)
        >>> control.correctionmode(option="both")
        >>> control.lowerlimit(0.0)
        >>> control.upperlimit(inf)
        >>> states.evaluatedvalue(3.0)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(1.0)

        |UpperLimit| is exclusive, while |LowerLimit| is inclusive:

        >>> control.upperlimit(3.0)
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(0.0)

        >>> control.lowerlimit(3.0)
        >>> control.upperlimit(inf)
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(1.0)

        Setting |Active| to |False| disables the correction completely:

        >>> control.active(False)
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(0.0)

        |CorrectionMode| restricts the correction to one simulation mode.  With
        `forecast`, the submodel does not correct the simulated values in the
        `historical` mode:

        >>> control.active(True)
        >>> control.correctionmode(option="forecast")
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(0.0)

        >>> pub.options.simulationmode = "forecast"
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(1.0)

        With `historical`, it is the other way round:

        >>> control.correctionmode(option="historical")
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(0.0)

        >>> pub.options.simulationmode = "historical"
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(1.0)
    """

    CONTROLPARAMETERS = (
        statcorr_control.Active,
        statcorr_control.CorrectionMode,
        statcorr_control.LowerLimit,
        statcorr_control.UpperLimit,
    )
    REQUIREDSEQUENCES = (statcorr_states.EvaluatedValue,)
    RESULTSEQUENCES = (statcorr_fluxes.IsActive,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if con.correctionmode == 3:
            modeallowed = True
        elif model.runsettings.simulationmode == modelutils.FORECAST:
            modeallowed = con.correctionmode == 2
        else:
            modeallowed = con.correctionmode == 1
        if (
            con.active
            and modeallowed
            and (con.lowerlimit <= sta.evaluatedvalue < con.upperlimit)
        ):
            flu.isactive = 1.0
        else:
            flu.isactive = 0.0


class Calc_Residual_ResidualAnchor_V1(modeltools.Method):
    r"""Determine the most recent pointwise residual (observed minus simulated
    value) and the corresponding simulated value while |Options.simulationmode| is
    `historical`.

    Basic equations:
      :math:`Residual = LoggedObservation_k - LoggedSimulation_k`

      :math:`ResidualAnchor = LoggedSimulation_k`

    :math:`k` denotes the most recent log index for which the observed value is not
    |numpy.nan|.  The search skips at most |MaxNaNSkip| preceding log entries with
    missing observations (or searches the entire log, whichever is smaller).  When
    no observation is available within that range, |Residual| and |ResidualAnchor|
    are set to zero, so no correction applies.

    While |Options.simulationmode| is `forecast`, |Calc_Residual_ResidualAnchor_V1|
    does not repeat the search and keeps both values of the most recent `historical`
    assessment.  Hence, the correction persists for the entire forecast horizon
    instead of vanishing as soon as the underlying log entry drops out of the
    logging window.

    Examples:

        If the most recent observation is available, it determines the residual:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import nan
        >>> control.maxnanskip(2)
        >>> derived.nmblogentries(3)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> logs.loggedsimulation = 5.0, 3.0, 2.0
        >>> logs.loggedobservation = 6.0, 4.0, 3.0
        >>> model.calc_residual_residualanchor_v1()
        >>> states.residual, states.residualanchor
        (residual(1.0), residualanchor(5.0))

        If the two most recent observations are missing, the residual stems from
        the third log entry:

        >>> logs.loggedobservation = nan, nan, 3.0
        >>> model.calc_residual_residualanchor_v1()
        >>> states.residual, states.residualanchor
        (residual(1.0), residualanchor(2.0))

        Restricting |MaxNaNSkip| so that the search does not reach this entry results
        in zero values:

        >>> control.maxnanskip(1)
        >>> model.calc_residual_residualanchor_v1()
        >>> states.residual, states.residualanchor
        (residual(0.0), residualanchor(0.0))

        A |MaxNaNSkip| value exceeding the log length is no problem:

        >>> control.maxnanskip(5)
        >>> model.calc_residual_residualanchor_v1()
        >>> states.residual, states.residualanchor
        (residual(1.0), residualanchor(2.0))

        In `forecast` mode, both values stay frozen:

        >>> pub.options.simulationmode = "forecast"
        >>> logs.loggedobservation = nan, nan, nan
        >>> model.calc_residual_residualanchor_v1()
        >>> states.residual, states.residualanchor
        (residual(1.0), residualanchor(2.0))
        >>> del pub.options.simulationmode
    """

    CONTROLPARAMETERS = (statcorr_control.MaxNaNSkip,)
    DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        statcorr_logs.LoggedSimulation,
        statcorr_logs.LoggedObservation,
    )
    UPDATEDSEQUENCES = (statcorr_states.Residual, statcorr_states.ResidualAnchor)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess
        if model.runsettings.simulationmode == modelutils.HISTORICAL:
            sta.residual = 0.0
            sta.residualanchor = 0.0
            for idx in range(min(der.nmblogentries, con.maxnanskip + 1)):
                if not modelutils.isnan(log.loggedobservation[idx]):
                    sta.residualanchor = log.loggedsimulation[idx]
                    sta.residual = log.loggedobservation[idx] - sta.residualanchor
                    break


class Calc_Stationary_V1(modeltools.Method):
    r"""Assess whether the observed values behave in a stationary way while the
    stationarity check is enabled (see |StationarityCheck|) and
    |Options.simulationmode| is `historical`.

    |Calc_Stationary_V1| takes the ratio of the minimum and the maximum
    |LoggedObservation| value within the most recent |StationarityWindow| log
    entries.  Whenever this ratio falls below |RatioMinMax|, it considers the
    conditions instationary (|Stationary| is ``0.0``), otherwise stationary
    (|Stationary| is ``1.0``).  If a |numpy.nan| value within the
    |StationarityWindow| prevents calculating the ratio, |Stationary| keeps the
    outcome of the previous assessment, so that a single missing observation does
    not change the outcome of the stationarity check (which decides on the
    reduction of the correction during forecast runs, see
    |Calc_ReductionFactor_V1|).

    While |Options.simulationmode| is `forecast`, |Calc_Stationary_V1| keeps the
    outcome of the most recent `historical` assessment.  Recomputing it would be
    unreliable, as |LoggedObservation| keeps receiving |numpy.nan| values
    throughout the forecast (see |Calc_OutputCorr_V1|), which would prevent any new
    assessment as soon as the first of them enters the |StationarityWindow|.

    Examples:

        The ratio ``4.0 / 5.0 = 0.8`` is not below |RatioMinMax|:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import nan
        >>> control.stationaritycheck(active=True, window=3, ratiominmax=0.5)
        >>> derived.stationaritywindow.update()
        >>> derived.ratiominmax.update()
        >>> derived.nmblogentries(3)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> logs.loggedobservation = 4.0, 5.0, 5.0
        >>> model.calc_stationary_v1()
        >>> states.stationary
        stationary(1.0)

        The ratio ``0.5 / 5.0 = 0.1`` is:

        >>> logs.loggedobservation = 0.5, 5.0, 5.0
        >>> model.calc_stationary_v1()
        >>> states.stationary
        stationary(0.0)

        A single missing observation within the |StationarityWindow| prevents a new
        assessment:

        >>> logs.loggedobservation = 4.0, nan, 5.0
        >>> model.calc_stationary_v1()
        >>> states.stationary
        stationary(0.0)

        In `forecast` mode, |Stationary| stays frozen:

        >>> pub.options.simulationmode = "forecast"
        >>> logs.loggedobservation = 4.0, 5.0, 5.0
        >>> model.calc_stationary_v1()
        >>> states.stationary
        stationary(0.0)

        The same holds when the stationarity check is disabled:

        >>> control.stationaritycheck(active=False)
        >>> derived.stationaritywindow.update()
        >>> pub.options.simulationmode = "historical"
        >>> model.calc_stationary_v1()
        >>> states.stationary
        stationary(0.0)
    """

    DERIVEDPARAMETERS = (
        statcorr_derived.NmbLogEntries,
        statcorr_derived.StationarityWindow,
        statcorr_derived.RatioMinMax,
    )
    REQUIREDSEQUENCES = (statcorr_logs.LoggedObservation,)
    UPDATEDSEQUENCES = (statcorr_states.Stationary,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess
        if (der.stationaritywindow > 0) and (
            model.runsettings.simulationmode == modelutils.HISTORICAL
        ):
            has_nan = False
            qmin: float = modelutils.inf
            qmax: float = -modelutils.inf
            for idx in range(min(der.nmblogentries, der.stationaritywindow)):
                value: float = log.loggedobservation[idx]
                if modelutils.isnan(value):
                    has_nan = True
                    break
                qmin = min(qmin, value)
                qmax = max(qmax, value)
            if not has_nan:
                if qmax > 0.0 and qmin / qmax < der.ratiominmax:
                    sta.stationary = 0.0
                else:
                    sta.stationary = 1.0


class Calc_ReductionFactor_V1(modeltools.Method):
    r"""Calculate the factor for damping the correction during forecast runs based
    on the outcome of the stationarity check.

    Basic equation (under instationary conditions in `forecast` mode):
      :math:`ReductionFactor = \max \left( 0, 1 -
      \frac{ForecastStep}{ReductionSteps} \right)`

    |ReductionFactor| is ``1.0`` while |Options.simulationmode| is `historical`, so
    the stationarity check never dampens the correction of `historical` runs.  In
    `forecast` mode, instationary conditions (|Stationary| is ``0.0``, as determined
    at the last `historical` step, see |Calc_Stationary_V1|) let |ReductionFactor|
    decrease linearly from ``1.0`` in the first forecast step to zero after
    |ReductionSteps| forecast steps (counted by |ForecastStep|).  Hence, the forecast
    starts with the unabated correction, avoiding a jump right at the start of the
    forecast horizon.  With stationary conditions or the stationarity check
    disabled (see |StationarityCheck|), |ReductionFactor| is always ``1.0``.

    Examples:

        In `historical` mode, |ReductionFactor| is ``1.0``, even under instationary
        conditions:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> control.reductionsteps(2)
        >>> derived.stationaritywindow(3)
        >>> states.stationary(0.0)
        >>> states.forecaststep(0.0)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> model.calc_reductionfactor_v1()
        >>> states.reductionfactor
        reductionfactor(1.0)

        In `forecast` mode, |ReductionFactor| decreases to zero within the two
        steps given by |ReductionSteps|:

        >>> pub.options.simulationmode = "forecast"
        >>> for forecaststep in range(4):
        ...     states.forecaststep(forecaststep)
        ...     model.calc_reductionfactor_v1()
        ...     print(forecaststep, states.reductionfactor.value)
        0 1.0
        1 0.5
        2 0.0
        3 0.0

        Setting |ReductionSteps| to zero reduces |ReductionFactor| to zero
        immediately:

        >>> control.reductionsteps(0)
        >>> states.forecaststep(0.0)
        >>> model.calc_reductionfactor_v1()
        >>> states.reductionfactor
        reductionfactor(0.0)

        Stationary conditions result in a |ReductionFactor| of ``1.0``:

        >>> states.stationary(1.0)
        >>> model.calc_reductionfactor_v1()
        >>> states.reductionfactor
        reductionfactor(1.0)

        The same holds when the stationarity check is disabled:

        >>> states.stationary(0.0)
        >>> derived.stationaritywindow(0)
        >>> model.calc_reductionfactor_v1()
        >>> states.reductionfactor
        reductionfactor(1.0)
        >>> del pub.options.simulationmode
    """

    CONTROLPARAMETERS = (statcorr_control.ReductionSteps,)
    DERIVEDPARAMETERS = (statcorr_derived.StationarityWindow,)
    REQUIREDSEQUENCES = (statcorr_states.Stationary, statcorr_states.ForecastStep)
    UPDATEDSEQUENCES = (statcorr_states.ReductionFactor,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        if (
            (model.runsettings.simulationmode == modelutils.HISTORICAL)
            or (der.stationaritywindow <= 0)
            or (sta.stationary == 1.0)
        ):
            sta.reductionfactor = 1.0
        elif con.reductionsteps <= 0:
            sta.reductionfactor = 0.0
        else:
            sta.reductionfactor = max(0.0, 1.0 - sta.forecaststep / con.reductionsteps)


class Calc_RelSumDelta_V1(modeltools.Method):
    r"""Calculate the relative sum of the absolute changes between successive
    simulated values while the variability check is enabled (see
    |StationarityCheck|) and |Options.simulationmode| is `historical`.

    Basic equation:
      :math:`RelSumDelta = \frac{1}{\overline{sim}}
      \sum_{i=0}^{EvaluationWindow-2}
      |LoggedSimulation_i - LoggedSimulation_{i+1}|`

      :math:`\overline{sim} = \frac{1}{EvaluationWindow}
      \sum_{i=0}^{EvaluationWindow-1} LoggedSimulation_i`

    The variability check assesses the simulated values only, so it relates their
    changes to their own mean (:math:`\overline{sim}`) within the |EvaluationWindow|.
    For a non-positive or missing :math:`\overline{sim}`, |RelSumDelta| is
    |numpy.nan|.  While |Options.simulationmode| is `forecast`,
    |Calc_RelSumDelta_V1| keeps the value of the most recent `historical`
    assessment.

    Examples:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> control.evaluationwindow(3)
        >>> derived.stationaryaveragingwindow(3)
        >>> derived.nmblogentries(3)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> logs.loggedsimulation = 9.0, 10.0, 11.0
        >>> model.calc_relsumdelta_v1()
        >>> states.relsumdelta
        relsumdelta(0.2)

        >>> logs.loggedsimulation = 0.0, 0.0, 0.0
        >>> model.calc_relsumdelta_v1()
        >>> states.relsumdelta
        relsumdelta(nan)

        In `forecast` mode or with the variability check disabled, |RelSumDelta|
        stays unchanged:

        >>> logs.loggedsimulation = 9.0, 10.0, 11.0
        >>> pub.options.simulationmode = "forecast"
        >>> model.calc_relsumdelta_v1()
        >>> states.relsumdelta
        relsumdelta(nan)

        >>> pub.options.simulationmode = "historical"
        >>> derived.stationaryaveragingwindow(0)
        >>> model.calc_relsumdelta_v1()
        >>> states.relsumdelta
        relsumdelta(nan)
    """

    CONTROLPARAMETERS = (statcorr_control.EvaluationWindow,)
    DERIVEDPARAMETERS = (statcorr_derived.StationaryAveragingWindow,)
    REQUIREDSEQUENCES = (statcorr_logs.LoggedSimulation,)
    UPDATEDSEQUENCES = (statcorr_states.RelSumDelta,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess
        if (der.stationaryaveragingwindow > 0) and (
            model.runsettings.simulationmode == modelutils.HISTORICAL
        ):
            sumdelta: float = 0.0
            for idx in range(con.evaluationwindow - 1):
                sumdelta = sumdelta + modelutils.fabs(
                    log.loggedsimulation[idx] - log.loggedsimulation[idx + 1]
                )
            sumsim: float = 0.0
            for idx in range(con.evaluationwindow):
                sumsim = sumsim + log.loggedsimulation[idx]
            meansim: float = sumsim / con.evaluationwindow
            if meansim > 0.0:
                sta.relsumdelta = sumdelta / meansim
            else:
                sta.relsumdelta = modelutils.nan


class Calc_LowVariability_V1(modeltools.Method):
    r"""Decide whether the simulated values vary little enough to use the
    |StationaryAveragingWindow| instead of the |AveragingWindow| (see
    |Calc_AveragedResidual_V1|).

    The variability check is only meaningful under stationary conditions.  Hence,
    it is part of the stationarity check (see |StationarityCheck|).  If enabled,
    |Calc_LowVariability_V1| considers the variability low (|LowVariability| is
    ``1.0``) if the stationarity check (see |Calc_Stationary_V1|) detects stationary
    conditions and |RelSumDelta| does not exceed |MaxRelSumDelta|.  Hence, the
    variability check never interferes with the linear reduction of the correction
    (see |Calc_ReductionFactor_V1|).  A |numpy.nan| value of |RelSumDelta| results
    in |LowVariability| being ``0.0``.  Like |Calc_RelSumDelta_V1|,
    |Calc_LowVariability_V1| reassesses |LowVariability| only while
    |Options.simulationmode| is `historical`.  With the stationarity check or the
    variability check disabled, |LowVariability| is always ``0.0``.

    Examples:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import nan
        >>> derived.stationaryaveragingwindow(3)
        >>> derived.maxrelsumdelta(0.2)
        >>> derived.stationaritywindow(3)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> states.stationary(1.0)
        >>> states.relsumdelta(0.2)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(1.0)

        >>> states.relsumdelta(0.4)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(0.0)

        >>> states.relsumdelta(nan)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(0.0)

        Instationary conditions according to the stationarity check prevent the
        variability check from detecting low variability:

        >>> states.relsumdelta(0.2)
        >>> states.stationary(0.0)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(0.0)

        In `forecast` mode, |LowVariability| stays frozen:

        >>> states.stationary(1.0)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(1.0)
        >>> pub.options.simulationmode = "forecast"
        >>> states.relsumdelta(0.4)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(1.0)

        Disabling the variability check or the stationarity check resets
        |LowVariability| to ``0.0``, even in `forecast` mode:

        >>> derived.stationaryaveragingwindow(0)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(0.0)

        >>> derived.stationaryaveragingwindow(3)
        >>> states.lowvariability(1.0)
        >>> derived.stationaritywindow(0)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(0.0)
        >>> del pub.options.simulationmode
    """

    DERIVEDPARAMETERS = (
        statcorr_derived.StationarityWindow,
        statcorr_derived.MaxRelSumDelta,
        statcorr_derived.StationaryAveragingWindow,
    )
    REQUIREDSEQUENCES = (statcorr_states.Stationary, statcorr_states.RelSumDelta)
    UPDATEDSEQUENCES = (statcorr_states.LowVariability,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        if (der.stationaritywindow <= 0) or (der.stationaryaveragingwindow <= 0):
            sta.lowvariability = 0.0
        elif model.runsettings.simulationmode == modelutils.HISTORICAL:
            if (sta.stationary == 1.0) and (sta.relsumdelta <= der.maxrelsumdelta):
                sta.lowvariability = 1.0
            else:
                sta.lowvariability = 0.0


class Calc_AveragedResidual_V1(modeltools.Method):
    r"""Determine the mean-value-based residual once, at the first forecast step,
    and freeze it for the remainder of the current forecast horizon.

    |Calc_AveragedResidual_V1| averages the |LoggedObservation| and
    |LoggedSimulation| entries covering the |AveragingWindow| log positions
    immediately preceding the current forecast run (log position ``0`` already holds
    the current forecast step's own values, so averaging starts at position ``1``)
    and stores their difference in |AveragedResidual|.  It leaves |AveragedResidual|
    unchanged whenever |Options.simulationmode| is `historical`, |ForecastStep| is
    not zero (i.e., beyond the first forecast step), or |AveragingWindow| is zero
    (mean-value-based correction disabled).  When the averaging window contains a
    |numpy.nan| value, it falls back to the pointwise |Residual| (see
    |Calc_Residual_ResidualAnchor_V1|).  While |LowVariability| is ``1.0`` (low
    variability according to the variability check, see |StationarityCheck|), the
    |StationaryAveragingWindow| replaces the |AveragingWindow|.

    Examples:

        On the first forecast step, the average is taken from log positions ``1``
        and ``2`` (mean observed ``4.0``, mean simulated ``3.0``):

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import nan
        >>> control.averagingwindow(2)
        >>> derived.stationaryaveragingwindow(1)
        >>> derived.nmblogentries(3)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "forecast"
        >>> states.forecaststep(0.0)
        >>> states.lowvariability(0.0)
        >>> states.residual(-9.0)
        >>> logs.loggedsimulation = 3.0, 2.0, 4.0
        >>> logs.loggedobservation = nan, 3.0, 5.0
        >>> model.calc_averagedresidual_v1()
        >>> states.averagedresidual
        averagedresidual(1.0)

        On any later forecast step and in `historical` mode, the previously
        determined value remains unchanged, regardless of the current log contents:

        >>> logs.loggedsimulation = 3.0, 20.0, 40.0
        >>> logs.loggedobservation = nan, 30.0, 50.0
        >>> states.forecaststep(1.0)
        >>> model.calc_averagedresidual_v1()
        >>> states.averagedresidual
        averagedresidual(1.0)

        >>> states.forecaststep(0.0)
        >>> pub.options.simulationmode = "historical"
        >>> model.calc_averagedresidual_v1()
        >>> states.averagedresidual
        averagedresidual(1.0)

        Setting |AveragingWindow| to zero disables mean-value-based correction:

        >>> pub.options.simulationmode = "forecast"
        >>> control.averagingwindow(0)
        >>> model.calc_averagedresidual_v1()
        >>> states.averagedresidual
        averagedresidual(1.0)

        A |numpy.nan| value within the averaging window makes
        |Calc_AveragedResidual_V1| fall back to |Residual|:

        >>> control.averagingwindow(2)
        >>> logs.loggedobservation = nan, nan, 50.0
        >>> model.calc_averagedresidual_v1()
        >>> states.averagedresidual
        averagedresidual(-9.0)

        Under low variability conditions (see |Calc_LowVariability_V1|), the averaging
        period covers the single log position ``1`` given by
        |StationaryAveragingWindow| (``30.0 - 20.0``), even if |AveragingWindow| is
        zero:

        >>> control.averagingwindow(0)
        >>> states.lowvariability(1.0)
        >>> logs.loggedobservation = nan, 30.0, nan
        >>> model.calc_averagedresidual_v1()
        >>> states.averagedresidual
        averagedresidual(10.0)
        >>> del pub.options.simulationmode
    """

    CONTROLPARAMETERS = (statcorr_control.AveragingWindow,)
    DERIVEDPARAMETERS = (
        statcorr_derived.NmbLogEntries,
        statcorr_derived.StationaryAveragingWindow,
    )
    REQUIREDSEQUENCES = (
        statcorr_logs.LoggedSimulation,
        statcorr_logs.LoggedObservation,
        statcorr_states.LowVariability,
        statcorr_states.ForecastStep,
        statcorr_states.Residual,
    )
    UPDATEDSEQUENCES = (statcorr_states.AveragedResidual,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.lowvariability == 1.0:
            nmb = min(der.stationaryaveragingwindow, der.nmblogentries - 1)
        else:
            nmb = min(con.averagingwindow, der.nmblogentries - 1)
        if (
            (model.runsettings.simulationmode == modelutils.FORECAST)
            and (sta.forecaststep == 0.0)
            and (nmb > 0)
        ):
            sum_obs: float = 0.0
            sum_sim: float = 0.0
            has_nan = False
            for idx in range(1, nmb + 1):
                obs_value: float = log.loggedobservation[idx]
                sim_value: float = log.loggedsimulation[idx]
                if modelutils.isnan(obs_value) or modelutils.isnan(sim_value):
                    has_nan = True
                    break
                sum_obs = sum_obs + obs_value
                sum_sim = sum_sim + sim_value
            if has_nan:
                sta.averagedresidual = sta.residual
            else:
                sta.averagedresidual = (sum_obs - sum_sim) / nmb


class Calc_CorrectedValue_V1(modeltools.Method):
    r"""Calculate the corrected value by shifting the current simulated value based
    on the (damped) residual.

    If the submodel is not responsible (|IsActive| is ``0.0``), the corrected value
    equals the current simulated value (:math:`sim_0`).  Otherwise, how the residual
    (:math:`r`) applies depends on how :math:`sim_0` compares to |ResidualAnchor|
    (:math:`sim_k`, the simulated value at the time the residual was determined),
    with :math:`f_{red}` denoting |ReductionFactor|:

     * If :math:`0 < sim_0 < sim_k`, |Calc_CorrectedValue_V1| shifts :math:`sim_0`
       *multiplicatively*, expressing the damped residual as a fraction of
       :math:`sim_k` and capping that fraction at |MaxRelShift|:

         :math:`CorrectedValue = sim_0 \cdot \left(1 + \mathrm{clip}\left(r \cdot
         f_{red} / sim_k,\ \pm MaxRelShift\right) \right)`

       Applying the residual as a fraction rather than a constant offset keeps the
       correction from overshooting or turning negative while the simulated values
       recede towards zero.

     * Otherwise (:math:`sim_0 \geq sim_k` or :math:`sim_0 \leq 0`), it shifts
       :math:`sim_0` *additively*, capping the damped residual at |MaxAbsShift|:

         :math:`CorrectedValue = sim_0 + \mathrm{clip}\left(r \cdot f_{red},\
         \pm MaxAbsShift\right)`

       This includes the `historical` mode whenever the current observation is
       available, as :math:`sim_k` then equals :math:`sim_0`.

    In `historical` mode (see |Options.simulationmode|), :math:`r` is the pointwise
    |Residual|.  In `forecast` mode, setting |AveragingWindow| to a value greater
    than zero (or |LowVariability| being ``1.0``) switches to the mean-value-based
    |AveragedResidual| (see |Calc_AveragedResidual_V1|).  Since it generally does
    not equal the pointwise residual at the forecast's start, switching to it
    abruptly would cause a jump in the corrected value right where the forecast
    begins.  To avoid this, |Calc_CorrectedValue_V1| starts every forecast run with the
    pointwise residual (so the corrected value picks up smoothly where the last
    measurement left off) and then linearly blends it towards the mean-value-based
    residual over |TransitionSteps| forecast steps (counted by |ForecastStep|),
    applying the mean-value-based residual unabated from then on:

        :math:`r = Residual + \min\left(1, \frac{ForecastStep}{TransitionSteps}
        \right) \cdot (AveragedResidual - Residual)`

    Examples:

        If the submodel is not responsible, no correction applies:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> control.maxabsshift(100.0)
        >>> control.maxrelshift(10.0)
        >>> control.averagingwindow(0)
        >>> control.transitionsteps(0)
        >>> derived.nmblogentries(1)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> fluxes.isactive = 0.0
        >>> states.reductionfactor(1.0)
        >>> states.lowvariability(0.0)
        >>> states.forecaststep(0.0)
        >>> states.averagedresidual(0.0)
        >>> states.residual(1.0)
        >>> states.residualanchor(5.0)
        >>> logs.loggedsimulation = 6.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(6.0)

        The current simulated value exceeds |ResidualAnchor|, so the residual
        applies additively:

        >>> fluxes.isactive = 1.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(7.0)

        |ReductionFactor| dampens the residual:

        >>> states.reductionfactor(0.5)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(6.5)

        |MaxAbsShift| caps the additive shift:

        >>> states.reductionfactor(1.0)
        >>> control.maxabsshift(0.2)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(6.2)

        For a *receding* simulation (the current simulated value is below
        |ResidualAnchor|), the residual applies multiplicatively:

        >>> control.maxabsshift(100.0)
        >>> states.residual(2.0)
        >>> states.residualanchor(10.0)
        >>> logs.loggedsimulation = 2.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(2.4)

        Limiting |MaxRelShift| to ``0.1`` caps that fraction at 10 % before it is
        converted back into an absolute shift:

        >>> control.maxrelshift(0.1)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(2.2)

        If the current simulated value equals |ResidualAnchor| (as in `historical`
        mode whenever the current observation is available), the residual applies
        additively, so |MaxRelShift| has no effect:

        >>> control.maxrelshift(0.0)
        >>> logs.loggedsimulation = 10.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(12.0)

        The same holds for a non-positive current simulated value:

        >>> logs.loggedsimulation = 0.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(2.0)
        >>> control.maxrelshift(10.0)

        Now, we demonstrate the transition from the pointwise residual (``1.0``)
        to the mean-value-based residual (``2.5``) over two forecast steps.  On the
        first forecast step, |Calc_CorrectedValue_V1| applies the pointwise residual
        unabated:

        >>> control.averagingwindow(2)
        >>> control.transitionsteps(2)
        >>> pub.options.simulationmode = "forecast"
        >>> states.residual(1.0)
        >>> states.residualanchor(8.0)
        >>> states.averagedresidual(2.5)
        >>> logs.loggedsimulation = 10.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(11.0)

        Halfway through the transition, the applied residual is the average of both
        (``1.75``):

        >>> states.forecaststep(1.0)
        >>> logs.loggedsimulation = 11.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(12.75)

        Once the transition period has elapsed, the full mean-value-based residual
        applies:

        >>> states.forecaststep(2.0)
        >>> logs.loggedsimulation = 12.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(14.5)

        Setting |TransitionSteps| to zero applies the mean-value-based residual
        immediately:

        >>> control.transitionsteps(0)
        >>> states.forecaststep(0.0)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(14.5)

        Under low variability conditions, the
        mean-value-based residual applies even if
        |AveragingWindow| is zero:

        >>> control.averagingwindow(0)
        >>> states.lowvariability(1.0)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(14.5)

        In `historical` mode, |Calc_CorrectedValue_V1| always relies on the pointwise
        residual, so that the corrected value reproduces the current observation:

        >>> pub.options.simulationmode = "historical"
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(13.0)
    """

    CONTROLPARAMETERS = (
        statcorr_control.MaxAbsShift,
        statcorr_control.MaxRelShift,
        statcorr_control.AveragingWindow,
        statcorr_control.TransitionSteps,
    )
    REQUIREDSEQUENCES = (
        statcorr_fluxes.IsActive,
        statcorr_logs.LoggedSimulation,
        statcorr_states.ReductionFactor,
        statcorr_states.LowVariability,
        statcorr_states.ForecastStep,
        statcorr_states.AveragedResidual,
        statcorr_states.Residual,
        statcorr_states.ResidualAnchor,
    )
    RESULTSEQUENCES = (statcorr_fluxes.CorrectedValue,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        sta = model.sequences.states.fastaccess
        sim: float = log.loggedsimulation[0]
        if flu.isactive == 0.0:
            flu.correctedvalue = sim
        else:
            residual: float = sta.residual
            if (model.runsettings.simulationmode == modelutils.FORECAST) and (
                (con.averagingwindow > 0) or (sta.lowvariability == 1.0)
            ):
                weight: float = 1.0
                if con.transitionsteps > 0:
                    weight = min(1.0, sta.forecaststep / con.transitionsteps)
                residual = residual + weight * (sta.averagedresidual - residual)
            residual = residual * sta.reductionfactor
            if 0.0 < sim < sta.residualanchor:
                flu.correctedvalue = sim + sim * min(
                    con.maxrelshift,
                    max(-con.maxrelshift, residual / sta.residualanchor),
                )
            else:
                flu.correctedvalue = sim + min(
                    con.maxabsshift, max(-con.maxabsshift, residual)
                )


class Update_ForecastStep_V1(modeltools.Method):
    r"""Count the forecast steps since the last `historical` simulation step.

    Basic equation:
      :math:`ForecastStep_{new} = \begin{cases}
      ForecastStep_{old} + 1 &|\ \text{forecast} \\
      0 &|\ \text{historical}
      \end{cases}`

    The case distinction refers to the current |Options.simulationmode|.

    Examples:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> states.forecaststep(0.0)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "forecast"
        >>> model.update_forecaststep_v1()
        >>> model.update_forecaststep_v1()
        >>> states.forecaststep
        forecaststep(2.0)

        >>> pub.options.simulationmode = "historical"
        >>> model.update_forecaststep_v1()
        >>> states.forecaststep
        forecaststep(0.0)
    """

    UPDATEDSEQUENCES = (statcorr_states.ForecastStep,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        sta = model.sequences.states.fastaccess
        if model.runsettings.simulationmode == modelutils.FORECAST:
            sta.forecaststep = sta.forecaststep + 1.0
        else:
            sta.forecaststep = 0.0


class Determine_OutputCorrection_V1(modeltools.AutoMethod):
    r"""Interface method that calculates the corrected value using an
    ARIMA(0,1,0) error model.

    |Determine_OutputCorrection_V1| executes the following submethods, which take
    the current simulation mode directly from |Options.simulationmode| (via
    |Model.runsettings|):

     * |Calc_EvaluatedValue_V1| and |Calc_IsActive_V1| decide whether the submodel
       is responsible for the current simulated value.
     * |Calc_Residual_ResidualAnchor_V1| determines the most recent pointwise
       residual.
     * |Calc_Stationary_V1| and |Calc_ReductionFactor_V1| dampen the correction under
       instationary conditions.
     * |Calc_RelSumDelta_V1|, |Calc_LowVariability_V1|, and
       |Calc_AveragedResidual_V1| determine the mean-value-based residual for
       forecast runs.
     * |Calc_CorrectedValue_V1| applies the resulting residual to the current simulated
       value.
     * |Update_ForecastStep_V1| counts the forecast steps.

    All submethods update the internal states even when the submodel is not
    responsible, so that a submodel taking over responsibility starts with
    up-to-date information.  While |Options.simulationmode| is `forecast`, they keep
    the outcomes of the most recent `historical` assessment (the responsibility, the
    pointwise residual, and the stationarity and variability assessments), so that
    only |ReductionFactor| and, if configured, the blend towards |AveragedResidual|
    can still change the correction once a forecast run is underway.

    Example:

        In `historical` mode, the correction reproduces the most recent
        observation:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import inf, nan
        >>> derived.nmblogentries(3)
        >>> control.evaluationwindow(3)
        >>> control.active(True)
        >>> control.correctionmode(option="both")
        >>> control.lowerlimit(0.0)
        >>> control.upperlimit(inf)
        >>> control.stationaritycheck(active=False)
        >>> derived.stationaritywindow.update()
        >>> derived.ratiominmax.update()
        >>> derived.maxrelsumdelta.update()
        >>> derived.stationaryaveragingwindow.update()
        >>> control.reductionsteps(2)
        >>> control.maxnanskip(2)
        >>> control.maxabsshift(100.0)
        >>> control.maxrelshift(10.0)
        >>> control.averagingwindow(0)
        >>> control.transitionsteps(0)
        >>> logs.loggedsimulation = 5.0, 3.0, 2.0
        >>> logs.loggedobservation = 6.0, 4.0, 3.0
        >>> model.determine_outputcorrection_v1()
        >>> fluxes.isactive
        isactive(1.0)
        >>> fluxes.correctedvalue
        correctedvalue(6.0)

        In `forecast` mode, the residual of the last `historical` step persists:

        >>> logs.loggedsimulation = 7.0, 5.0, 3.0
        >>> logs.loggedobservation = nan, 6.0, 4.0
        >>> from hydpy import pub
        >>> with pub.options.simulationmode("forecast"):
        ...     model.determine_outputcorrection_v1()
        >>> fluxes.correctedvalue
        correctedvalue(8.0)
        >>> states.forecaststep
        forecaststep(1.0)
    """

    SUBMETHODS = (
        Calc_EvaluatedValue_V1,
        Calc_IsActive_V1,
        Calc_Residual_ResidualAnchor_V1,
        Calc_Stationary_V1,
        Calc_ReductionFactor_V1,
        Calc_RelSumDelta_V1,
        Calc_LowVariability_V1,
        Calc_AveragedResidual_V1,
        Calc_CorrectedValue_V1,
        Update_ForecastStep_V1,
    )
    CONTROLPARAMETERS = (
        statcorr_control.Active,
        statcorr_control.CorrectionMode,
        statcorr_control.LowerLimit,
        statcorr_control.UpperLimit,
        statcorr_control.EvaluationWindow,
        statcorr_control.MaxNaNSkip,
        statcorr_control.MaxAbsShift,
        statcorr_control.MaxRelShift,
        statcorr_control.AveragingWindow,
        statcorr_control.TransitionSteps,
        statcorr_control.ReductionSteps,
    )
    DERIVEDPARAMETERS = (
        statcorr_derived.NmbLogEntries,
        statcorr_derived.StationarityWindow,
        statcorr_derived.RatioMinMax,
        statcorr_derived.MaxRelSumDelta,
        statcorr_derived.StationaryAveragingWindow,
    )
    REQUIREDSEQUENCES = (
        statcorr_logs.LoggedSimulation,
        statcorr_logs.LoggedObservation,
    )
    UPDATEDSEQUENCES = (
        statcorr_states.EvaluatedValue,
        statcorr_states.ReductionFactor,
        statcorr_states.Stationary,
        statcorr_states.RelSumDelta,
        statcorr_states.LowVariability,
        statcorr_states.ForecastStep,
        statcorr_states.AveragedResidual,
        statcorr_states.Residual,
        statcorr_states.ResidualAnchor,
    )
    RESULTSEQUENCES = (statcorr_fluxes.IsActive, statcorr_fluxes.CorrectedValue)


class Is_Active_V1(modeltools.Method):
    """Tell whether the submodel corrected the simulated value during the most
    recent call of |Determine_OutputCorrection_V1|.

    Example:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> fluxes.isactive = 1.0
        >>> assert model.is_active_v1()
        >>> fluxes.isactive = 0.0
        >>> assert not model.is_active_v1()
    """

    REQUIREDSEQUENCES = (statcorr_fluxes.IsActive,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> bool:
        flu = model.sequences.fluxes.fastaccess
        return flu.isactive == 1.0


class Get_CorrectedOutput_V1(modeltools.Method):
    """Return the most recently calculated corrected value.

    Example:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> fluxes.correctedvalue = 2.5
        >>> from hydpy import round_
        >>> round_(model.get_correctedoutput_v1())
        2.5
    """

    REQUIREDSEQUENCES = (statcorr_fluxes.CorrectedValue,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> float:
        flu = model.sequences.fluxes.fastaccess
        return flu.correctedvalue


class Model(modeltools.AdHocModel):
    """|statcorr.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="StatCorr")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = (Pick_OriginalQ_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (Calc_OutputCorr_V1,)
    INTERFACE_METHODS = (
        Set_SimulatedValue_V1,
        Set_ObservedValue_V1,
        Determine_OutputCorrection_V1,
        Is_Active_V1,
        Get_CorrectedOutput_V1,
    )
    ADD_METHODS = (
        Calc_OutputCorr_OutputCorrModel_V1,
        Calc_EvaluatedValue_V1,
        Calc_IsActive_V1,
        Calc_Residual_ResidualAnchor_V1,
        Calc_Stationary_V1,
        Calc_ReductionFactor_V1,
        Calc_RelSumDelta_V1,
        Calc_LowVariability_V1,
        Calc_AveragedResidual_V1,
        Calc_CorrectedValue_V1,
        Update_ForecastStep_V1,
    )
    OUTLET_METHODS = (Pass_CorrectedQ_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (statcorrinterfaces.OutputCorrModel_V1,)
    SUBMODELS = ()

    outputcorrmodels = modeltools.SubmodelsProperty(
        statcorrinterfaces.OutputCorrModel_V1
    )


class Main_OutputCorrModel_V1(modeltools.AdHocModel):
    """Base class for |statcorr.DOCNAME.long| models that use submodels that comply
    with the |OutputCorrModel_V1| interface."""

    outputcorrmodels: modeltools.SubmodelsProperty[
        statcorrinterfaces.OutputCorrModel_V1
    ]

    @importtools.prepare_submodel(  # type: ignore[call-overload, untyped-decorator]
        "outputcorrmodels", statcorrinterfaces.OutputCorrModel_V1, dimensionality=1
    )
    def add_outputcorrmodel_v1(
        self,
        outputcorrmodel: statcorrinterfaces.OutputCorrModel_V1,
        /,
        *,
        position: int,
        refresh: bool,
    ) -> None:
        """Initialise the given submodel that follows the |OutputCorrModel_V1|
        interface.

        The main model does not need to pass any information to the submodel.  In
        particular, the submodel determines the length of its log from its own
        parameters (see |NmbLogEntries|):

        >>> from hydpy.models.statcorr_main import *
        >>> parameterstep()
        >>> nmbsubmodels(1)
        >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0):
        ...     evaluationwindow(2)
        ...     stationaritycheck(active=True, window=4, ratiominmax=0.5)
        ...     maxnanskip(2)
        ...     averagingwindow(0)
        >>> model.outputcorrmodels[0].parameters.derived.nmblogentries
        nmblogentries(4)
        >>> model.outputcorrmodels[0].sequences.logs.loggedsimulation
        loggedsimulation(nan, nan, nan, nan)
        """


class Sub_OutputCorrModel(modeltools.AdHocModel):
    """Base class for submodels that comply with the submodel interfaces defined in
    module |statcorrinterfaces|."""
