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
    """Let all |OutputCorrModel_V1| submodels correct the current simulated
    discharge and take the result of the last responsible one.

    Each submodel decides on its own whether it is responsible (see
    |OutputCorrModel_V1.is_active|).  If none is, |CorrectedQ| equals |OriginalQ|.
    In `forecast` mode (see |Options.simulationmode|), |Calc_OutputCorr_V1| passes
    |numpy.nan| instead of |Discharge| to the submodels, which then rely on the
    information logged during the preceding `historical` run (see |statcorr_main|).

    Examples:

        Without any submodel, |CorrectedQ| equals |OriginalQ|:

        >>> from hydpy.models.statcorr_main import *
        >>> parameterstep()
        >>> fluxes.originalq = 3.5
        >>> inputs.discharge = 2.5
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(3.5)

        We attach two |statcorr_arima010| submodels responsible for observed
        discharges below and above 3 m³/s, respectively:

        >>> from numpy import inf
        >>> nmbsubmodels(2)
        >>> for i, limits in enumerate(((0.0, 3.0), (3.0, inf))):
        ...     with model.add_outputcorrmodel_v1("statcorr_arima010", position=i):
        ...         active(True)
        ...         correctionmode(option="both")
        ...         lowerlimit(limits[0])
        ...         upperlimit(limits[1])
        ...         evaluationwindow(1)
        ...         maxnanskip(2)
        ...         maxabsshift(100.0)
        ...         maxrelshift(10.0)
        ...         averagingwindow(0)
        ...         transitionsteps(0)
        ...         stationaritycheck(active=False)
        ...         reductionsteps(1)

        For an observed discharge of 2.5 m³/s, only the first submodel is
        responsible.  The second one does not overwrite its result:

        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(2.5)

        For an observed discharge of 4.0 m³/s, the second submodel takes over:

        >>> fluxes.originalq = 2.5
        >>> inputs.discharge = 4.0
        >>> model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(4.0)

        In `forecast` mode, the actual |Discharge| value is ignored, and the
        responsible submodel applies its last residual:

        >>> from hydpy import pub
        >>> fluxes.originalq = 3.0
        >>> inputs.discharge = 999.0
        >>> with pub.options.simulationmode("forecast"):
        ...     model.calc_outputcorr_v1()
        >>> fluxes.correctedq
        correctedq(4.5)
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
    output.

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
    r"""Calculate the mean of the most recent observed values.

    Basic equation:
      :math:`EvaluatedValue = \frac{1}{n}
      \sum_{i=0}^{EvaluationWindow-1} LoggedObservation_i`

    If all values are |numpy.nan|, |EvaluatedValue| keeps its
    previous value.  The same holds in `forecast` mode.

    Example:

        The mean of the first three log entries without the missing one is `3.0`:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import nan
        >>> control.evaluationwindow(3)
        >>> derived.nmblogentries(5)
        >>> logs.loggedobservation = 1.0, nan, 5.0, 8.0, 9.0
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
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

    The submodel is responsible if |Active| is |True|, |CorrectionMode| allows a
    correction in the current simulation mode (see |Options.simulationmode|), and
    |EvaluatedValue| (:math:`\overline{obs}`) lies within its value range:

      :math:`LowerLimit \leq \overline{obs} < UpperLimit`

    For a |numpy.nan| value of |EvaluatedValue|, the submodel is not responsible.

    Examples:

        |LowerLimit| is inclusive:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> control.active(True)
        >>> control.correctionmode(option="both")
        >>> control.lowerlimit(3.0)
        >>> control.upperlimit(5.0)
        >>> states.evaluatedvalue(3.0)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(1.0)

        With |CorrectionMode| set to `forecast`, the submodel is responsible only in
        `forecast` mode:

        >>> control.correctionmode(option="forecast")
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(0.0)
        >>> pub.options.simulationmode = "forecast"
        >>> model.calc_isactive_v1()
        >>> fluxes.isactive
        isactive(1.0)
        >>> del pub.options.simulationmode
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
    r"""Determine the most recent residual (observed minus simulated value) and
    the corresponding simulated value.

    Basic equations:
      :math:`Residual = LoggedObservation_k - LoggedSimulation_k`

      :math:`ResidualAnchor = LoggedSimulation_k`

    :math:`k` is the most recent log index with an available observation.  The
    search skips at most |MaxNaNSkip| missing observations.  If it finds no
    observation, |Residual| and |ResidualAnchor| are zero.  In `forecast` mode (see
    |Options.simulationmode|), both keep their previous values.

    Examples:

        The two most recent observations are missing, so the residual stems from
        the third log entry:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
        >>> from numpy import nan
        >>> control.maxnanskip(2)
        >>> derived.nmblogentries(3)
        >>> from hydpy import pub
        >>> pub.options.simulationmode = "historical"
        >>> logs.loggedsimulation = 5.0, 3.0, 2.0
        >>> logs.loggedobservation = nan, nan, 3.0
        >>> model.calc_residual_residualanchor_v1()
        >>> states.residual, states.residualanchor
        (residual(1.0), residualanchor(2.0))

        With |MaxNaNSkip| set to one, the search does not reach this entry:

        >>> control.maxnanskip(1)
        >>> model.calc_residual_residualanchor_v1()
        >>> states.residual, states.residualanchor
        (residual(0.0), residualanchor(0.0))
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
    r"""Check whether the observed values are stationary.

    Basic equation:
      :math:`Stationary = \begin{cases}
      0 &|\ min / max < RatioMinMax \
      1 &|\ else
      \end{cases}`

    :math:`min` and :math:`max` are the smallest and the largest |LoggedObservation|
    value within the |StationarityWindow|.  If this window contains a |numpy.nan|
    value, |Stationary| keeps its previous value.  The same holds in `forecast` mode
    (see |Options.simulationmode|) and if the stationarity check is disabled (see
    |StationarityCheck|).

    Examples:

        The ratio `4.0 / 5.0 = 0.8` is not below |RatioMinMax|:

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

        The ratio `0.5 / 5.0 = 0.1` is:

        >>> logs.loggedobservation = 0.5, 5.0, 5.0
        >>> model.calc_stationary_v1()
        >>> states.stationary
        stationary(0.0)

        A missing observation within the |StationarityWindow| prevents a new
        assessment:

        >>> logs.loggedobservation = 4.0, nan, 5.0
        >>> model.calc_stationary_v1()
        >>> states.stationary
        stationary(0.0)
        >>> del pub.options.simulationmode
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
    r"""Calculate the factor for reducing the correction in forecast mode under
    instationary conditions.

    Basic equation:
      :math:`ReductionFactor = \max \left( 0, 1 -
      \frac{ForecastStep}{ReductionSteps} \right)`

    The equation applies only in `forecast` mode (see |Options.simulationmode|) and
    only if |Stationary| is `0.0` (see |Calc_Stationary_V1|).  Then,
    |ReductionFactor| decreases linearly from `1.0` to zero within |ReductionSteps|
    forecast steps.  In all other cases, including a disabled stationarity check
    (see |StationarityCheck|), |ReductionFactor| is `1.0`.

    Examples:

        In `historical` mode, |ReductionFactor| is `1.0`, even under instationary
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

        Stationary conditions result in a |ReductionFactor| of `1.0`:

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

    Basic equation:
      :math:`LowVariability = \begin{cases}
      1 &|\ Stationary = 1 \ \land \ RelSumDelta \leq MaxRelSumDelta \
      0 &|\ else
      \end{cases}`

    With the stationarity check or the variability check disabled (see
    |StationarityCheck|), |LowVariability| is always `0.0`.  In `forecast` mode, it
    keeps its previous value.

    Examples:

        >>> from hydpy.models.statcorr import *
        >>> parameterstep()
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

        >>> states.stationary(0.0)
        >>> model.calc_lowvariability_v1()
        >>> states.lowvariability
        lowvariability(0.0)

        Disabling the variability check resets |LowVariability| to `0.0`, even in
        `forecast` mode:

        >>> pub.options.simulationmode = "forecast"
        >>> states.lowvariability(1.0)
        >>> derived.stationaryaveragingwindow(0)
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

    This method averages |LoggedObservation| and |LoggedSimulation| over the
    |AveragingWindow| and stores the difference in |AveragedResidual|.
    If |Options.simulationmode| is `historical`, or |ForecastStep| is
    not zero, |AveragedResidual| is unchanged. When the averaging window contains a
    |numpy.nan| value, it falls back to the pointwise |Residual|.  If |LowVariability|
    is `1.0`, |StationaryAveragingWindow| replaces |AveragingWindow|.

    Examples:

        On the first forecast step, the average is taken from log positions `1`
        and `2` (mean observed `4.0`, mean simulated `3.0`):

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

        A |numpy.nan| value within the averaging window results in |Residual|:

        >>> logs.loggedobservation = nan, nan, 5.0
        >>> model.calc_averagedresidual_v1()
        >>> states.averagedresidual
        averagedresidual(-9.0)

        Under low variability conditions, |StationaryAveragingWindow| (here, the
        single log position `1`) applies, even if |AveragingWindow| is zero:

        >>> control.averagingwindow(0)
        >>> states.lowvariability(1.0)
        >>> logs.loggedsimulation = 3.0, 20.0, 40.0
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

    If the submodel is not responsible (|IsActive| is `0.0`), the corrected value
    equals the current simulated value (:math:`sim_0`).  Otherwise, the residual
    (:math:`r`), damped by |ReductionFactor| (:math:`f_{red}`), applies
    multiplicatively if :math:`sim_0` recedes below |ResidualAnchor|
    (:math:`sim_k`) and additively otherwise.  The multiplicative variant keeps the
    correction from overshooting or turning negative while the simulated values
    recede towards zero.

    Basic equations:
      :math:`CorrectedValue = sim_0 \cdot \left(1 + \mathrm{clip}\left(r \cdot
      f_{red} / sim_k,\ \pm MaxRelShift\right) \right) \quad | \quad 0 < sim_0 <
      sim_k`

      :math:`CorrectedValue = sim_0 + \mathrm{clip}\left(r \cdot f_{red},\
      \pm MaxAbsShift\right) \quad | \quad else`

    In `historical` mode (see |Options.simulationmode|), :math:`r` is the pointwise
    |Residual|.  In `forecast` mode, a positive |AveragingWindow| (or |LowVariability|
    being `1.0`) lets :math:`r` blend linearly from |Residual| to |AveragedResidual|
    over |TransitionSteps| forecast steps, which avoids a jump at the forecast's
    start:

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
        >>> states.reductionfactor(0.5)
        >>> states.lowvariability(0.0)
        >>> states.forecaststep(0.0)
        >>> states.averagedresidual(0.0)
        >>> states.residual(1.0)
        >>> states.residualanchor(5.0)
        >>> logs.loggedsimulation = 6.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(6.0)

        The current simulated value exceeds |ResidualAnchor|, so the damped
        residual applies additively, capped by |MaxAbsShift|:

        >>> fluxes.isactive = 1.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(6.5)
        >>> control.maxabsshift(0.2)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(6.2)

        For a receding simulation, the residual applies multiplicatively, capped by
        |MaxRelShift|:

        >>> states.reductionfactor(1.0)
        >>> states.residual(2.0)
        >>> states.residualanchor(10.0)
        >>> logs.loggedsimulation = 2.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(2.4)
        >>> control.maxrelshift(0.1)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(2.2)

        Halfway through a forecast transition from the pointwise residual (`1.0`)
        to the mean-value-based residual (`2.5`), their average (`1.75`) applies:

        >>> control.maxabsshift(100.0)
        >>> control.averagingwindow(2)
        >>> control.transitionsteps(2)
        >>> pub.options.simulationmode = "forecast"
        >>> states.residual(1.0)
        >>> states.residualanchor(8.0)
        >>> states.averagedresidual(2.5)
        >>> states.forecaststep(1.0)
        >>> logs.loggedsimulation = 11.0
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(12.75)

        Under low variability conditions, the mean-value-based residual also
        applies for a zero |AveragingWindow|, and without delay for zero
        |TransitionSteps|:

        >>> control.averagingwindow(0)
        >>> control.transitionsteps(0)
        >>> states.lowvariability(1.0)
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(13.5)

        In `historical` mode, only the pointwise residual counts:

        >>> pub.options.simulationmode = "historical"
        >>> model.calc_correctedvalue_v1()
        >>> fluxes.correctedvalue
        correctedvalue(12.0)
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
    """Determine the corrected value based on the residuals between the observed and
    the simulated values."""

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
