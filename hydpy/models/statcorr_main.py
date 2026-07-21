# pylint: disable=unused-wildcard-import
"""
|statcorr_main| applies statistical output correction to discharge forecasts.  It reads
the simulated discharge from its inlet node(s), passes it through one or more
|OutputCorrModel_V1| submodels (e.g. |statcorr_arima010|), and delivers the corrected
discharge to the outlet node.

Integration test
================

    .. how_to_understand_integration_tests::

    We prepare a simulation period of six days:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-07", "1d"

    >>> from hydpy.models.statcorr_main import *
    >>> parameterstep()

    We connect the model to a single inlet and outlet node and set up the test object:

    >>> from hydpy import Element, IntegrationTest
    >>> element = Element("element", inlets="inlet", outlets="outlet")
    >>> element.model = model

    We configure a logging window of three time steps and attach a single
    |statcorr_arima010| submodel.  Setting |QminQmax| to zero disables the LARSIM
    stationarity check (any quotient of the measured discharge's minimum and
    maximum is at least zero), so the ARIMA correction always applies unabated:

    >>> loggingwindow(3)
    >>> nmboutputcorrmodels(1)
    >>> propagatecorrection(True)
    >>> with model.add_outputcorrmodel_v1(
    ...     "statcorr_arima010", position=0
    ... ) as submodel:
    ...     submodel.parameters.control.corrnq(True)
    ...     submodel.parameters.control.corrmq(True)
    ...     submodel.parameters.control.corrhq(True)
    ...     submodel.parameters.control.limitnqm(0.0)
    ...     submodel.parameters.control.limitmqh(100.0)
    ...     submodel.parameters.control.evaluationwindow(3)
    ...     submodel.parameters.control.maxresiduallookback(3)
    ...     submodel.parameters.control.maxabsoluteshift(100.0)
    ...     submodel.parameters.control.maxrelativeshift(1000.0)
    ...     submodel.parameters.control.residualaveragingwindow(0)
    ...     submodel.parameters.control.residualtransitiontime(0)
    ...     submodel.parameters.control.qminqmax(0.0)
    ...     submodel.parameters.control.nqmstationaritywindow(3)
    ...     submodel.parameters.control.linearreductiontime(1, 1)

    >>> test = IntegrationTest(element)

    The inlet provides the simulated discharge; |Discharge| carries the observations.
    Observations are available for the first two steps only, simulating a forecast
    period starting on day three:

    >>> from numpy import nan
    >>> element.inlets.inlet.sequences.sim.series = 1.0, 2.0, 3.0, 4.0, 5.0, 6.0
    >>> with pub.options.checkseries(False):
    ...     inputs.discharge.series = 1.5, 2.5, nan, nan, nan, nan

    During the first two steps the correction is based on the concurrent residual
    (``0.5``).  In the forecast period the model falls back to the most recent
    available residual, which stays at ``0.5`` until it drops out of the logging
    window on day five, after which no correction is applied:

.. integration-test::

    >>> test.dateformat = '%d/%m %H:00'
    >>> test()
    |        date | discharge | inflow | correctedq | inlet | outlet |
    ------------------------------------------------------------------
    | 01/01 00:00 |       1.5 |    1.0 |        1.5 |   1.0 |    1.5 |
    | 02/01 00:00 |       2.5 |    2.0 |        2.5 |   2.0 |    2.5 |
    | 03/01 00:00 |       nan |    3.0 |        3.5 |   3.0 |    3.5 |
    | 04/01 00:00 |       nan |    4.0 |        4.5 |   4.0 |    4.5 |
    | 05/01 00:00 |       nan |    5.0 |        5.0 |   5.0 |    5.0 |
    | 06/01 00:00 |       nan |    6.0 |        6.0 |   6.0 |    6.0 |
"""

from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import statcorrinterfaces
from hydpy.models.statcorr import statcorr_control
from hydpy.models.statcorr import statcorr_model

ADDITIONAL_CONTROLPARAMETERS = (
    statcorr_control.LoggingWindow,
    statcorr_control.NmbOutputCorrModels,
    statcorr_control.PropagateCorrection,
)


class Model(modeltools.AdHocModel):
    """|statcorr_main.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Statcorr-Main",
        description="main statistical output correction model for discharge forecasts",
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (statcorr_model.Pick_Inflow_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (statcorr_model.Calc_OutputCorr_V1,)
    INTERFACE_METHODS = (statcorr_model.Get_Discharge_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = (statcorr_model.Pass_CorrectedQ_V1,)
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
        log allocation."""
        nmb = int(self.parameters.control.loggingwindow.value)
        outputcorrmodel.parameters.control.loggingwindow(nmb)
        outputcorrmodel.prepare_nmblogentries(nmb)


tester = Tester()
cythonizer = Cythonizer()
