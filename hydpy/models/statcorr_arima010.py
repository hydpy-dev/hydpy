# pylint: disable=unused-wildcard-import
"""
|statcorr_arima010| performs statistical output correction of simulated values
based on an ARIMA(0,1,0) error model.

The corrected value is derived from the most recently available residual
(observed minus simulated values).  While |Options.simulationmode| equals
`historical`, this residual is (re)determined every step by searching back at
most |MaxNaNSkip| log entries for the latest non-|numpy.nan|
observation — this is the random-walk persistence of the error whenever the
*current* observation is missing.  When no observation is available within
that range (or the entire log, whichever is smaller), no correction is
applied.  While |Options.simulationmode| equals `forecast`, this search is
not repeated: the residual (and the simulated value it was measured
against) stays frozen at whatever the most recent `historical` assessment
found, so the correction persists throughout the whole forecast horizon
(subject only to |ReductionFactor|) instead of fading once that log entry
ages past |MaxNaNSkip|.

How the residual is applied depends on how the current simulated value
compares to the simulated value at the point the residual was determined:
if it is higher, the residual is added unchanged (capped at
|MaxAbsShift|); otherwise, it is applied as a percentage of that anchor
value instead (capped at |MaxRelShift|), which keeps the correction from
overshooting or turning negative while the simulated values recede.  See
|Determine_OutputCorrection_V1| for the exact formulas.

Setting |AveragingWindow| to a value greater than zero switches from
that pointwise residual to a mean-value-based one (mean observed minus mean
simulated values over the given number of log entries immediately
preceding the current forecast run), blended in linearly over
|TransitionSteps| forecast steps to avoid a jump right where the
forecast begins.  See |Determine_OutputCorrection_V1| and
|Calc_AveragedResidual_V1| for details.

Each |statcorr_arima010| instance is responsible for a specific value range
only, defined by |LowerLimit| and |UpperLimit|, and can be switched off completely
via |Active| or restricted to one simulation mode via |CorrectionMode|.
Optionally, |StationarityCheck| lets it fade out the correction under instationary
conditions, and |VariabilityCheck| lets it base the mean-value-based residual on a
separate averaging period under stationary conditions.

|statcorr_arima010| serves as a submodel for |statcorr| and complies with the
|OutputCorrModel_V1| interface.

Example workflow
================

    |statcorr_arima010| determines the length of its internal log from its
    parameters (see |NmbLogEntries|) and resizes both the simulated and the
    observed values log accordingly:

    >>> from hydpy.models.statcorr_arima010 import *
    >>> parameterstep()
    >>> from numpy import inf
    >>> control.active(True)
    >>> control.correctionmode("both")
    >>> control.lowerlimit(0.0)
    >>> control.upperlimit(inf)
    >>> control.evaluationwindow(3)
    >>> control.stationaritycheck(False)
    >>> derived.stationaritywindow.update()
    >>> derived.ratiominmax.update()
    >>> control.variabilitycheck(False)
    >>> derived.maxrelsumdelta.update()
    >>> derived.stationaryaveragingwindow.update()
    >>> control.reductionsteps(1)
    >>> control.maxnanskip(3)
    >>> control.maxabsshift(100.0)
    >>> control.maxrelshift(1000.0)
    >>> control.averagingwindow(0)
    >>> control.transitionsteps(0)
    >>> derived.nmblogentries.update()
    >>> derived.nmblogentries
    nmblogentries(3)
    >>> logs.loggedsimulatedvalue
    loggedsimulatedvalue(nan, nan, nan)
    >>> logs.loggedobservedvalue
    loggedobservedvalue(nan, nan, nan)

    Successive calls of |OutputCorrModel_V1.set_simulatedvalue| and
    |OutputCorrModel_V1.set_observedvalue| shift the previously buffered
    values one position to the right and store the new value at position 0:

    >>> model.set_simulatedvalue(2.0)
    >>> model.set_observedvalue(3.0)
    >>> model.set_simulatedvalue(3.0)
    >>> model.set_observedvalue(4.0)
    >>> model.set_simulatedvalue(5.0)
    >>> from numpy import nan
    >>> model.set_observedvalue(nan)
    >>> logs.loggedsimulatedvalue
    loggedsimulatedvalue(5.0, 3.0, 2.0)
    >>> logs.loggedobservedvalue
    loggedobservedvalue(nan, 4.0, 3.0)

    |OutputCorrModel_V1.determine_outputcorrection| computes the corrected
    value from the random-walk residual (here taken from log position 1,
    since position 0 has no observation) and stores it internally;
    |OutputCorrModel_V1.is_active| confirms the submodel is responsible for the
    current value, and |OutputCorrModel_V1.get_correctedoutput| returns the
    buffered value:

    >>> model.determine_outputcorrection(False)
    >>> assert model.is_active()
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
        short="StatCorr-ARIMA010",
        description="ARIMA(0,1,0) — random walk — output correction ",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        statcorr_model.Set_SimulatedValue_V1,
        statcorr_model.Set_ObservedValue_V1,
        statcorr_model.Determine_OutputCorrection_V1,
        statcorr_model.Is_Active_V1,
        statcorr_model.Get_CorrectedOutput_V1,
    )
    ADD_METHODS = (statcorr_model.Calc_AveragedResidual_V1,)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
