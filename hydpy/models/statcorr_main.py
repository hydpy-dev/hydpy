# pylint: disable=unused-wildcard-import
"""
|statcorr_main| applies statistical output correction to discharge forecasts.  It reads
the simulated discharge from its inlet node(s), passes it through one or more
|OutputCorrModel_V1| submodels (e.g. |statcorr_arima010|), and delivers the corrected
discharge to the outlet node.

Integration tests
=================

    .. how_to_understand_integration_tests::

    he exact functionality of the submodels is illustrated in their integration tests.
    The main model, `statcorr_main`, serves as a container for the submodels. This
    section demonstrates how submodels with different parameterizations can be combined
    using the main model.

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
    >>> test.dateformat = "%Y-%m-%d"

    We attach a two submodels to the main model. For both submodels, `lowerlimit` is
    `0.0` and `upperlimit` is `inf`, so the correction should take place for any
    observed discharge. Both submodels should correct the discharge only in forecast
    mode. For the second submodel, we limit th ecorrection by setting |MaxAbsShift| to
    `0.5` and |MaxRelShift| to `0.05`.

    >>> from numpy import inf, nan
    >>> nmbsubmodels(2)
    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0) as sub:
    ...     control = sub.parameters.control
    ...     control.active(True)
    ...     control.correctionmode(option="forecast")
    ...     control.lowerlimit(0.0)
    ...     control.upperlimit(inf)
    ...     control.evaluationwindow(1)
    ...     control.maxnanskip(2)
    ...     control.maxabsshift(100.0)
    ...     control.maxrelshift(10.0)
    ...     control.minvalue(-inf)
    ...     control.maxvalue(inf)
    ...     control.averagingwindow(0)
    ...     control.transitionsteps(0)
    ...     control.stationaritycheck(active=False)
    ...     control.reductionsteps(1)
    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=1) as sub:
    ...     control = sub.parameters.control
    ...     control.active(True)
    ...     control.correctionmode(option="forecast")
    ...     control.lowerlimit(0.0)
    ...     control.upperlimit(inf)
    ...     control.evaluationwindow(1)
    ...     control.maxnanskip(2)
    ...     control.maxabsshift(0.5)
    ...     control.maxrelshift(0.05)
    ...     control.minvalue(-inf)
    ...     control.maxvalue(inf)
    ...     control.averagingwindow(0)
    ...     control.transitionsteps(0)
    ...     control.stationaritycheck(active=False)
    ...     control.reductionsteps(1)

    We specify a time series with simulated values for the entire period and a
    time series with observations for the first five time steps.

    >>> element.inlets.inlet.sequences.sim.series = (
    ...     8.0, 9.0, 10.0, 10.0, 10.0, 11.0, 12.0, 9.0, 6.0, 3.0
    ... )
    >>> with pub.options.checkseries(False):
    ...     model.sequences.inputs.discharge.series = (
    ...         [9.6, 10.8, 12.6, 12.0, 12.0] + 5 * [nan]
    ...     )

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
    ...         test.hydpy.simulate()
    ...     conditions = model.conditions
    ...     pub.timegrids.sim.dates = split, last
    ...     with pub.options.simulationmode("forecast"):
    ...         model.conditions = conditions
    ...         test.hydpy.simulate()
    ...     pub.timegrids.sim.dates = first, last
    ...     test.print_table()

    Since the last submodel, which would perform a correction, is given priority, the
    correction is limited according to the parameters of the second submodel:

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        8.0 |   8.0 |    8.0 |
    | 2000-01-02 |      10.8 |       9.0 |        9.0 |   9.0 |    9.0 |
    | 2000-01-03 |      12.6 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-01-04 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-01-05 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-01-06 |       nan |      11.0 |       11.5 |  11.0 |   11.5 |
    | 2000-01-07 |       nan |      12.0 |       12.5 |  12.0 |   12.5 |
    | 2000-01-08 |       nan |       9.0 |       9.45 |   9.0 |   9.45 |
    | 2000-01-09 |       nan |       6.0 |        6.3 |   6.0 |    6.3 |
    | 2000-01-10 |       nan |       3.0 |       3.15 |   3.0 |   3.15 |

    Now we change the correction mode for the first submodel to "both". We see
    that in historical mode, the first submodel now does the correction, while in
    forecast mode, the second submodel still has priority:

    >>> model.outputcorrmodels[0].parameters.control.correctionmode(option="both")

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-01-02 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-01-03 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-01-04 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-01-05 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-01-06 |       nan |      11.0 |       11.5 |  11.0 |   11.5 |
    | 2000-01-07 |       nan |      12.0 |       12.5 |  12.0 |   12.5 |
    | 2000-01-08 |       nan |       9.0 |       9.45 |   9.0 |   9.45 |
    | 2000-01-09 |       nan |       6.0 |        6.3 |   6.0 |    6.3 |
    | 2000-01-10 |       nan |       3.0 |       3.15 |   3.0 |   3.15 |

    Increasing the |LowerLimit| of the second submodel to `15.0` means that
    the correction is now performed by the first submodel even in prediction mode.

    >>> model.outputcorrmodels[0].parameters.control.lowerlimit(15.0)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        8.0 |   8.0 |    8.0 |
    | 2000-01-02 |      10.8 |       9.0 |        9.0 |   9.0 |    9.0 |
    | 2000-01-03 |      12.6 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-01-04 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-01-05 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-01-06 |       nan |      11.0 |       11.5 |  11.0 |   11.5 |
    | 2000-01-07 |       nan |      12.0 |       12.5 |  12.0 |   12.5 |
    | 2000-01-08 |       nan |       9.0 |       9.45 |   9.0 |   9.45 |
    | 2000-01-09 |       nan |       6.0 |        6.3 |   6.0 |    6.3 |
    | 2000-01-10 |       nan |       3.0 |       3.15 |   3.0 |   3.15 |


"""

from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import statcorrinterfaces
from hydpy.models.statcorr import statcorr_model


class Model(statcorr_model.Main_OutputCorrModel_V1):
    """|statcorr_main.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="StatCorr-Main",
        description="main statistical output correction model for discharge forecasts",
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (statcorr_model.Pick_OriginalQ_V1,)
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


tester = Tester()
cythonizer = Cythonizer()
