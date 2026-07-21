# pylint: disable=unused-wildcard-import
"""
|statcorr_arima010| performs statistical output correction of discharge forecasts
based on an ARIMA(0,1,0) error model.

The corrected discharge is derived from the most recently available residual
(observed minus simulated discharge).  When the current observation is
|numpy.nan| (typical in forecast mode), the correction falls back to the most
recent past residual within the configured logging window — this is the
random-walk persistence of the error.  This fallback search looks back at most
|MaxResidualLookback| log entries; when no observation is available within
that range (or the entire log, whichever is smaller), no correction is applied.

How the residual is applied depends on how the current simulated discharge
compares to the simulated discharge at the point the residual was determined:
if it is higher, the residual is added unchanged (capped at
|MaxAbsoluteShift|); otherwise, it is applied as a percentage of that anchor
value instead (capped at |MaxRelativeShift|), which keeps the correction from
overshooting or turning negative while the discharge recedes.  See
|Determine_OutputCorrection_V1| for the exact formulas.

Setting |ResidualAveragingWindow| to a value greater than zero switches from
that pointwise residual to a mean-value-based one (mean observed minus mean
simulated discharge over the given number of log entries immediately
preceding the current forecast run), blended in linearly over
|ResidualTransitionTime| forecast steps to avoid a jump right where the
forecast begins.  See |Determine_OutputCorrection_V1| and
|Calc_AveragedResidual_V1| for details.

|statcorr_arima010| serves as a submodel for |statcorr| and complies with the
|OutputCorrModel_V1| interface.

Example workflow
================

    Allocating the internal log resizes both the simulated and the observed
    discharge log to the requested number of entries:

    >>> from hydpy.models.statcorr_arima010 import *
    >>> parameterstep()
    >>> control.corrnq(True)
    >>> control.corrmq(True)
    >>> control.corrhq(True)
    >>> control.limitnqm(3.0)
    >>> control.limitmqh(5.0)
    >>> control.evaluationwindow(3)
    >>> control.qminqmax(0.0)
    >>> control.nqmstationaritywindow(3)
    >>> control.linearreductiontime(1, 1)
    >>> control.maxresiduallookback(3)
    >>> control.maxabsoluteshift(100.0)
    >>> control.maxrelativeshift(1000.0)
    >>> control.residualaveragingwindow(0)
    >>> control.residualtransitiontime(0)
    >>> model.prepare_nmblogentries(3)
    >>> derived.nmblogentries
    nmblogentries(3)
    >>> logs.loggedsimulateddischarge
    loggedsimulateddischarge(nan, nan, nan)
    >>> logs.loggedobserveddischarge
    loggedobserveddischarge(nan, nan, nan)

    Successive calls of |OutputCorrModel_V1.set_simulateddischarge| and
    |OutputCorrModel_V1.set_observeddischarge| shift the previously buffered
    values one position to the right and store the new value at position 0:

    >>> model.set_simulateddischarge(2.0)
    >>> model.set_observeddischarge(3.0)
    >>> model.set_simulateddischarge(3.0)
    >>> model.set_observeddischarge(4.0)
    >>> model.set_simulateddischarge(5.0)
    >>> from numpy import nan
    >>> model.set_observeddischarge(nan)
    >>> logs.loggedsimulateddischarge
    loggedsimulateddischarge(5.0, 3.0, 2.0)
    >>> logs.loggedobserveddischarge
    loggedobserveddischarge(nan, 4.0, 3.0)

    |OutputCorrModel_V1.determine_outputcorrection| computes the corrected
    discharge from the random-walk residual (here taken from log position 1,
    since position 0 has no observation) and stores it internally;
    |OutputCorrModel_V1.get_correctedoutput| returns the buffered value:

    >>> model.determine_outputcorrection(False)
    >>> from hydpy import round_
    >>> round_(model.get_correctedoutput())
    6.0
"""

from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import statcorrinterfaces
from hydpy.models.statcorr import statcorr_derived
from hydpy.models.statcorr import statcorr_model

ADDITIONAL_DERIVEDPARAMETERS = (statcorr_derived.NmbLogEntries,)


class Model(statcorr_model.Sub_OutputCorrModel, statcorrinterfaces.OutputCorrModel_V1):
    """|statcorr_arima010.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Statcorr-ARIMA010",
        description="ARIMA(0,1,0) — random walk — output correction for discharge",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        statcorr_model.Set_SimulatedDischarge_V1,
        statcorr_model.Set_ObservedDischarge_V1,
        statcorr_model.Determine_OutputCorrection_V1,
        statcorr_model.Get_CorrectedOutput_V1,
    )
    ADD_METHODS = (statcorr_model.Calc_AveragedResidual_V1,)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    def prepare_nmblogentries(self, nmblogentries: int) -> None:
        """Allocate the internal log to hold `nmblogentries` discharge values and
        initialise |ReductionFactor|, |Stationary|, |FlowCondition|,
        |ForecastStep|, and |AveragedResidual| to ``1.0``, ``1.0``, ``2.0``,
        ``0.0``, and ``0.0`` (no reduction, stationary conditions assumed, HQ
        flow condition assumed, no forecast steps elapsed, no mean-value-based
        residual determined yet).

        >>> from hydpy.models.statcorr_arima010 import *
        >>> parameterstep()
        >>> model.prepare_nmblogentries(4)
        >>> derived.nmblogentries
        nmblogentries(4)
        >>> logs.loggedsimulateddischarge
        loggedsimulateddischarge(nan, nan, nan, nan)
        >>> logs.loggedobserveddischarge
        loggedobserveddischarge(nan, nan, nan, nan)
        >>> states.reductionfactor
        reductionfactor(1.0)
        >>> states.stationary
        stationary(1.0)
        >>> states.flowcondition
        flowcondition(2.0)
        >>> states.forecaststep
        forecaststep(0.0)
        >>> states.averagedresidual
        averagedresidual(0.0)
        """
        self.parameters.derived.nmblogentries(nmblogentries)
        self.sequences.logs.loggedsimulateddischarge.shape = nmblogentries
        self.sequences.logs.loggedobserveddischarge.shape = nmblogentries
        self.sequences.states.reductionfactor(1.0)
        self.sequences.states.stationary(1.0)
        self.sequences.states.flowcondition(2.0)
        self.sequences.states.forecaststep(0.0)
        self.sequences.states.averagedresidual(0.0)


tester = Tester()
cythonizer = Cythonizer()
