# pylint: disable=unused-wildcard-import
"""
|statcorr_main| applies statistical output correction to discharge forecasts.  It reads
the simulated discharge from its inlet node(s), passes it through one or more
|OutputCorrModel_V1| submodels (e.g. |statcorr_arima010|), and delivers the corrected
discharge to the outlet node.

Integration tests
=================

    .. how_to_understand_integration_tests::

    We prepare a simulation period of ten days:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-11", "1d"

    >>> from hydpy.models.statcorr_main import *
    >>> parameterstep()

    We connect the model to a single inlet and outlet node and set up the test object:

    >>> from hydpy import Element, IntegrationTest
    >>> element = Element("element", inlets="inlet", outlets="outlet")
    >>> element.model = model
    >>> propagate(True)
    >>> test = IntegrationTest(element)
    >>> test.dateformat = "%d/%m"

    The following function configures a |statcorr_arima010| submodel with the
    settings shared by all examples.  It makes the submodel responsible for all
    discharges (its |EvaluationWindow| of one step means it assesses its
    responsibility based on the current simulated discharge only) and disables the
    stationarity check via |StationarityCheck|, the variability check via
    |VariabilityCheck|, and the mean-value-based residual via |AveragingWindow|, so
    the ARIMA correction always applies unabated.  The individual examples
    override some of these settings:

    >>> from numpy import inf, nan
    >>> def configure(submodel):
    ...     control = submodel.parameters.control
    ...     control.active(True)
    ...     control.correctionmode(option="both")
    ...     control.lowerlimit(0.0)
    ...     control.upperlimit(inf)
    ...     control.evaluationwindow(1)
    ...     control.maxnanskip(2)
    ...     control.maxabsshift(100.0)
    ...     control.maxrelshift(10.0)
    ...     control.averagingwindow(0)
    ...     control.transitionsteps(0)
    ...     control.stationaritycheck(active=False)
    ...     control.variabilitycheck(active=False)
    ...     control.reductionsteps(1)

    The inlet provides the simulated discharge; |Discharge| carries the
    observations.

Historical simulation
_____________________

    We attach a single submodel:

    >>> nmbsubmodels(1)
    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0) as sub:
    ...     configure(sub)

    In the first example, the complete simulation period runs in `historical`
    mode.  Observations are available for the first two days only:

    >>> element.inlets.inlet.sequences.sim.series = range(1, 11)
    >>> with pub.options.checkseries(False):
    ...     inputs.discharge.series = 1.5, 2.5, nan, nan, nan, nan, nan, nan, nan, nan

    During the first two steps the correction is based on the concurrent residual
    (``0.5``).  Afterwards, the model falls back to the most recent available
    residual, which stays at ``0.5`` until it lies more than |MaxNaNSkip| entries
    back on day five, after which no correction is applied:

.. integration-test::

    >>> test()
    |  date | discharge | inflow | correctedq | inlet | outlet |
    ------------------------------------------------------------
    | 01/01 |       1.5 |    1.0 |        1.5 |   1.0 |    1.5 |
    | 02/01 |       2.5 |    2.0 |        2.5 |   2.0 |    2.5 |
    | 03/01 |       nan |    3.0 |        3.5 |   3.0 |    3.5 |
    | 04/01 |       nan |    4.0 |        4.5 |   4.0 |    4.5 |
    | 05/01 |       nan |    5.0 |        5.0 |   5.0 |    5.0 |
    | 06/01 |       nan |    6.0 |        6.0 |   6.0 |    6.0 |
    | 07/01 |       nan |    7.0 |        7.0 |   7.0 |    7.0 |
    | 08/01 |       nan |    8.0 |        8.0 |   8.0 |    8.0 |
    | 09/01 |       nan |    9.0 |        9.0 |   9.0 |    9.0 |
    | 10/01 |       nan |   10.0 |       10.0 |  10.0 |   10.0 |

Forecast simulation
___________________

    In operational use, a forecast consists of two separate simulation runs.  First,
    a `historical` run covers the period with observations and ends with saving the
    current conditions (the states and logs of all submodels).  Second, a
    `forecast` run starts from these conditions and covers the forecast horizon.
    The following function emulates this workflow by splitting the simulation
    period at the given date, switching |Options.simulationmode| in between, and
    printing the results of both runs in a single table:

    >>> def forecast_test(split):
    ...     test.prepare_model(update_parameters=True, use_conditions=None)
    ...     first, last = pub.timegrids.sim.firstdate, pub.timegrids.sim.lastdate
    ...     pub.timegrids.sim.lastdate = split
    ...     with pub.options.simulationmode("historical"):
    ...         model.update_parameters()
    ...         test.hydpy.simulate()
    ...     conditions = model.conditions
    ...     pub.timegrids.sim.dates = split, last
    ...     with pub.options.simulationmode("forecast"):
    ...         model.update_parameters()
    ...         model.conditions = conditions
    ...         test.hydpy.simulate()
    ...     pub.timegrids.sim.dates = first, last
    ...     test.print_table()

    We replace the submodel of the previous example with a fresh one and let the
    forecast start on day six.  In contrast to the previous example, observations
    are available for all days.  However, |Calc_OutputCorr_V1| ignores them during
    the `forecast` run.  Instead, the submodel keeps applying the residual
    determined at the end of the `historical` run (``6.0 - 5.0 = 1.0``) throughout
    the whole forecast horizon, even after it lies more than |MaxNaNSkip| entries
    back:

    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0) as sub:
    ...     configure(sub)
    >>> with pub.options.checkseries(False):
    ...     inputs.discharge.series = 1.5, 2.5, 3.5, 4.5, 6.0, 9.0, 9.0, 9.0, 9.0, 9.0

.. integration-test::

    >>> forecast_test("2000-01-06")
    |  date | discharge | inflow | correctedq | inlet | outlet |
    ------------------------------------------------------------
    | 01/01 |       1.5 |    1.0 |        1.5 |   1.0 |    1.5 |
    | 02/01 |       2.5 |    2.0 |        2.5 |   2.0 |    2.5 |
    | 03/01 |       3.5 |    3.0 |        3.5 |   3.0 |    3.5 |
    | 04/01 |       4.5 |    4.0 |        4.5 |   4.0 |    4.5 |
    | 05/01 |       6.0 |    5.0 |        6.0 |   5.0 |    6.0 |
    | 06/01 |       9.0 |    6.0 |        7.0 |   6.0 |    7.0 |
    | 07/01 |       9.0 |    7.0 |        8.0 |   7.0 |    8.0 |
    | 08/01 |       9.0 |    8.0 |        9.0 |   8.0 |    9.0 |
    | 09/01 |       9.0 |    9.0 |       10.0 |   9.0 |   10.0 |
    | 10/01 |       9.0 |   10.0 |       11.0 |  10.0 |   11.0 |

Mean-value-based residual
_________________________

    Setting |AveragingWindow| to two makes the submodel determine a mean-value-based
    residual from the two days preceding the forecast (days four and five, mean
    observed ``5.0``, mean simulated ``4.5``, hence ``0.5``).  Setting
    |TransitionSteps| to two makes the applied residual change linearly from the
    pointwise residual (``1.0``) to the mean-value-based residual over the first two
    forecast steps:

    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0) as sub:
    ...     configure(sub)
    ...     averagingwindow(2)
    ...     transitionsteps(2)
    >>> with pub.options.checkseries(False):
    ...     inputs.discharge.series = 1.5, 2.5, 3.5, 4.0, 6.0, nan, nan, nan, nan, nan

.. integration-test::

    >>> forecast_test("2000-01-06")
    |  date | discharge | inflow | correctedq | inlet | outlet |
    ------------------------------------------------------------
    | 01/01 |       1.5 |    1.0 |        1.5 |   1.0 |    1.5 |
    | 02/01 |       2.5 |    2.0 |        2.5 |   2.0 |    2.5 |
    | 03/01 |       3.5 |    3.0 |        3.5 |   3.0 |    3.5 |
    | 04/01 |       4.0 |    4.0 |        4.0 |   4.0 |    4.0 |
    | 05/01 |       6.0 |    5.0 |        6.0 |   5.0 |    6.0 |
    | 06/01 |       nan |    6.0 |        7.0 |   6.0 |    7.0 |
    | 07/01 |       nan |    7.0 |       7.75 |   7.0 |   7.75 |
    | 08/01 |       nan |    8.0 |        8.5 |   8.0 |    8.5 |
    | 09/01 |       nan |    9.0 |        9.5 |   9.0 |    9.5 |
    | 10/01 |       nan |   10.0 |       10.5 |  10.0 |   10.5 |

Stationarity check
__________________

    Next, we enable the stationarity check with a window of three days and a
    |RatioMinMax| of ``0.5``, and set |ReductionSteps| to four.  The simulated
    discharge is constant.  On day five, the observations of days three to five
    (``5.5``, ``8.0``, and ``3.0``) become instationary (``3.0 / 8.0 < 0.5``), so
    |ReductionFactor| starts to decrease linearly.  It continues to do so during the
    `forecast` run, which reuses the assessment of the `historical` run, until the
    correction vanishes completely:

    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0) as sub:
    ...     configure(sub)
    ...     stationaritycheck(active=True, window=3, ratiominmax=0.5)
    ...     reductionsteps(4)
    >>> element.inlets.inlet.sequences.sim.series = 5.0
    >>> with pub.options.checkseries(False):
    ...     inputs.discharge.series = 5.5, 5.5, 5.5, 8.0, 3.0, nan, nan, nan, nan, nan

.. integration-test::

    >>> forecast_test("2000-01-06")
    |  date | discharge | inflow | correctedq | inlet | outlet |
    ------------------------------------------------------------
    | 01/01 |       5.5 |    5.0 |        5.5 |   5.0 |    5.5 |
    | 02/01 |       5.5 |    5.0 |        5.5 |   5.0 |    5.5 |
    | 03/01 |       5.5 |    5.0 |        5.5 |   5.0 |    5.5 |
    | 04/01 |       8.0 |    5.0 |        8.0 |   5.0 |    8.0 |
    | 05/01 |       3.0 |    5.0 |        3.5 |   5.0 |    3.5 |
    | 06/01 |       nan |    5.0 |        4.0 |   5.0 |    4.0 |
    | 07/01 |       nan |    5.0 |        4.5 |   5.0 |    4.5 |
    | 08/01 |       nan |    5.0 |        5.0 |   5.0 |    5.0 |
    | 09/01 |       nan |    5.0 |        5.0 |   5.0 |    5.0 |
    | 10/01 |       nan |    5.0 |        5.0 |   5.0 |    5.0 |

Variability check
_________________

    Now, we enable the variability check instead, with a |MaxRelSumDelta| of
    ``0.1`` and an averaging period of four days, and set |EvaluationWindow| to
    three and |AveragingWindow| to one.  During the first two days, the
    |EvaluationWindow| still contains missing values, so the submodel does not
    consider itself responsible.  As the simulated discharge is constant, the
    variability check detects stationary conditions, so the mean-value-based
    residual relies on the four days preceding the forecast (mean observed
    ``6.25``, mean simulated ``5.0``) instead of on the single day given by
    |AveragingWindow| (which would result in ``1.0``):

    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0) as sub:
    ...     configure(sub)
    ...     evaluationwindow(3)
    ...     averagingwindow(1)
    ...     variabilitycheck(active=True, maxrelsumdelta=0.1, averagingwindow=4)
    >>> with pub.options.checkseries(False):
    ...     inputs.discharge.series = 6.0, 6.0, 6.0, 7.0, 6.0, nan, nan, nan, nan, nan

.. integration-test::

    >>> forecast_test("2000-01-06")
    |  date | discharge | inflow | correctedq | inlet | outlet |
    ------------------------------------------------------------
    | 01/01 |       6.0 |    5.0 |        5.0 |   5.0 |    5.0 |
    | 02/01 |       6.0 |    5.0 |        5.0 |   5.0 |    5.0 |
    | 03/01 |       6.0 |    5.0 |        6.0 |   5.0 |    6.0 |
    | 04/01 |       7.0 |    5.0 |        7.0 |   5.0 |    7.0 |
    | 05/01 |       6.0 |    5.0 |        6.0 |   5.0 |    6.0 |
    | 06/01 |       nan |    5.0 |       6.25 |   5.0 |   6.25 |
    | 07/01 |       nan |    5.0 |       6.25 |   5.0 |   6.25 |
    | 08/01 |       nan |    5.0 |       6.25 |   5.0 |   6.25 |
    | 09/01 |       nan |    5.0 |       6.25 |   5.0 |   6.25 |
    | 10/01 |       nan |    5.0 |       6.25 |   5.0 |   6.25 |

Multiple submodels
__________________

    Finally, we attach two submodels responsible for different discharge ranges.
    The first one handles simulated discharges below ``5.0`` and the second one all
    others.  The second one restricts the relative shift to 5 % and the absolute
    shift to ``0.25``:

    >>> nmbsubmodels(2)
    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0) as sub:
    ...     configure(sub)
    ...     upperlimit(5.0)
    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=1) as sub:
    ...     configure(sub)
    ...     lowerlimit(5.0)
    ...     maxrelshift(0.05)
    ...     maxabsshift(0.25)
    >>> element.inlets.inlet.sequences.sim.series = (
    ...     1.0, 2.0, 6.0, 7.0, 3.0, 4.0, 6.0, 8.0, 4.0, 3.0
    ... )
    >>> with pub.options.checkseries(False):
    ...     inputs.discharge.series = 1.5, 2.5, 8.0, 9.0, 3.5, nan, nan, nan, nan, nan

    During the `historical` run, the second submodel takes over on days three and
    four, where its restricted absolute shift prevents reproducing the observations
    (the relative shift does not apply, as the current observation is available,
    see |Calc_CorrectedQ_V1|).  During the `forecast` run, the responsible submodel
    does not change (see |EvaluatedValue|).  Hence, the first submodel, which was
    responsible at the end of the `historical` run, keeps applying the residual of
    ``0.5`` unrestricted, even when the forecasted discharge exceeds ``5.0``:

.. integration-test::

    >>> forecast_test("2000-01-06")
    |  date | discharge | inflow | correctedq | inlet | outlet |
    ------------------------------------------------------------
    | 01/01 |       1.5 |    1.0 |        1.5 |   1.0 |    1.5 |
    | 02/01 |       2.5 |    2.0 |        2.5 |   2.0 |    2.5 |
    | 03/01 |       8.0 |    6.0 |       6.25 |   6.0 |   6.25 |
    | 04/01 |       9.0 |    7.0 |       7.25 |   7.0 |   7.25 |
    | 05/01 |       3.5 |    3.0 |        3.5 |   3.0 |    3.5 |
    | 06/01 |       nan |    4.0 |        4.5 |   4.0 |    4.5 |
    | 07/01 |       nan |    6.0 |        6.5 |   6.0 |    6.5 |
    | 08/01 |       nan |    8.0 |        8.5 |   8.0 |    8.5 |
    | 09/01 |       nan |    4.0 |        4.5 |   4.0 |    4.5 |
    | 10/01 |       nan |    3.0 |        3.5 |   3.0 |    3.5 |
"""

from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import statcorrinterfaces
from hydpy.models.statcorr import statcorr_control
from hydpy.models.statcorr import statcorr_model

ADDITIONAL_CONTROLPARAMETERS = (
    statcorr_control.NmbSubmodels,
    statcorr_control.Propagate,
)


class Model(modeltools.AdHocModel):
    """|statcorr_main.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="StatCorr-Main",
        description="main statistical output correction model for discharge forecasts",
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (statcorr_model.Pick_Inflow_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (statcorr_model.Calc_OutputCorr_V1,)
    INTERFACE_METHODS = ()
    ADD_METHODS = (statcorr_model.Calc_OutputCorr_OutputCorrModel_V1,)
    OUTLET_METHODS = (statcorr_model.Pass_CorrectedQ_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (statcorrinterfaces.OutputCorrModel_V1,)
    SUBMODELS = ()

    outputcorrmodels = modeltools.SubmodelsProperty(
        statcorrinterfaces.OutputCorrModel_V1
    )

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

        The submodel determines the length of its log from its own parameters (see
        |NmbLogEntries|), so the main model does not need to pass any information.
        """


tester = Tester()
cythonizer = Cythonizer()
