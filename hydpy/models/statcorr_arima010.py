# pylint: disable=unused-wildcard-import
"""
The |statcorr.DOCNAME.long| model family member |statcorr_arima010| is an output
correction submodel that follows the LARSIM approach for forecast correction based
on the difference between observed and simulated values.

Integration tests
=================

    .. how_to_understand_integration_tests::

    |statcorr_arima010| receives all its input from a main model.  Hence, we use it
    as a submodel of |statcorr_main| for the following tests.  |statcorr_main| is
    meant to correct discharge, so in this integration test, we use discharge as
    the corrected variable. |statcorr_arima010| can be used to correct all variables
    with a true zero point, though.

    We prepare a simulation period of ten days and connect the main model to an inlet
    and an outlet node.

    >>> from hydpy import Element, IntegrationTest, prepare_model, pub
    >>> pub.timegrids = "2000-01-01", "2000-01-11", "1d"
    >>> model = prepare_model("statcorr_main")
    >>> element = Element("element", inlets="inlet", outlets="outlet")
    >>> element.model = model
    >>> model.parameters.control.propagate(True)
    >>> model.parameters.control.nmbsubmodels(1)

    We attach a |statcorr_arima010| submodel.  We differentiate between two
    operating modes: `historical` and `forecast`.  `correctionmode(option="both"` means
    that the correction will take place in historical and in forecast more.  The effect
    of the correction candiffer between the two modes.

    The correction will only take place if the mean of the observation in the
    evaluation window lies between `lowerlimit` and `upperlimit`.

    We set `evaluationwindow(1)` so only the last observation value will be evaluated
    for the decision if the submodel will do the correction. The submodel is only
    active if the mean discharge in the evaluation period is between `lowerlimit`
    and `upperlimit`. With `lowerlimit(0.0)` and upperlimit(inf), the correction will
    take place for any value of the observation.

    We set `averagingwindow(0)`, so the single most recent observation will be used
    to calculate the residual which is the base for the correction. This corresponds to
    the behaviour of the LARSIM option `WHM-ARIMA-VORHERSAGE`.

    If the last observation is NaN, we search for an available observed value up to
    two time steps earlier (`maxnanskip(2)`).

    We set the maximum absolute shift to `100.0` and the maximum relative shift
    to `10.0`. The other parameters are set to zero or False so they are inactive for
    now, we explain their effect later.

    >>> from numpy import inf, nan
    >>> with model.add_outputcorrmodel_v1("statcorr_arima010", position=0):
    ...     active(True)
    ...     correctionmode(option="both")
    ...     lowerlimit(0.0)
    ...     upperlimit(inf)
    ...     evaluationwindow(1)
    ...     maxnanskip(2)
    ...     maxabsshift(100.0)
    ...     maxrelshift(1.0)
    ...     minvalue(-inf)
    ...     maxvalue(inf)
    ...     averagingwindow(0)
    ...     transitionsteps(0)
    ...     stationaritycheck(active=False)
    ...     reductionsteps(1)
    >>> test = IntegrationTest(element)
    >>> test.dateformat = "%Y-%d-%m"

    The following function first runs a `historical` simulation until the given
    date.  Then, it runs a `forecast` simulation for the remaining days, starting
    from the conditions of the `historical` run:

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

    The observed discharge for the fifth day is `10.0`, and the simulated discharge
    is `12.0`, so the last residual is `2.0` (remember, we set `evaluationwindow(1)`:

    >>> element.inlets.inlet.sequences.sim.series = (
    ...     8.0, 9.0, 10.0, 10.0, 10.0, 11.0, 12.0, 9.0, 6.0, 3.0
    ... )
    >>> with pub.options.checkseries(False):
    ...     model.sequences.inputs.discharge.series = (
    ...         [9.6, 10.8, 12.6, 12.0, 12.0] + 5 * [nan]
    ...     )

Additive and relative shift
___________________________

    If the simulated discharge is greater than the observed discharge at the
    forecast start (the mean over the evaluation period), the correction uses an
    absolute shift (limited to `maxabsshift`), otherwise a relative shift (limited
    to `maxrelshift`).

    In the historical mode, the corrected value is the observed value of this time
    step.

    We see that as long as the simulated discharge is not below `10.0` (the simulated
    value when the residual was determined), the submodel adds the residual.  When the
    simulated discharge falls below `10.0`, the submodel applies the residual as
    a relative shift (`2.0 / 10.0 = 20 %`).  So, the correction becomes smaller
    when the discharge decreases:

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-04-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.0 |  11.0 |   13.0 |
    | 2000-07-01 |       nan |      12.0 |       14.0 |  12.0 |   14.0 |
    | 2000-08-01 |       nan |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-09-01 |       nan |       6.0 |        7.2 |   6.0 |    7.2 |
    | 2000-10-01 |       nan |       3.0 |        3.6 |   3.0 |    3.6 |

Limited relative shift
______________________

    Now, we limit the relative shift to 10 % with |MaxRelShift|.  The first two
    forecast days do not change, because the submodel adds the residual there.  On
    the last three days, the correction is limited to 10 %:

    >>> model.outputcorrmodels[0].parameters.control.maxrelshift(0.1)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-04-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.0 |  11.0 |   13.0 |
    | 2000-07-01 |       nan |      12.0 |       14.0 |  12.0 |   14.0 |
    | 2000-08-01 |       nan |       9.0 |        9.9 |   9.0 |    9.9 |
    | 2000-09-01 |       nan |       6.0 |        6.6 |   6.0 |    6.6 |
    | 2000-10-01 |       nan |       3.0 |        3.3 |   3.0 |    3.3 |

Limited absolute shift
______________________

    The absolute shift can be limited as well: now, we set |MaxAbsShift|
    to `1.0 m³/s`:

    >>> model.outputcorrmodels[0].parameters.control.maxabsshift(1.0)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.0 |   8.0 |    9.0 |
    | 2000-02-01 |      10.8 |       9.0 |       10.0 |   9.0 |   10.0 |
    | 2000-03-01 |      12.6 |      10.0 |       11.0 |  10.0 |   11.0 |
    | 2000-04-01 |      12.0 |      10.0 |       11.0 |  10.0 |   11.0 |
    | 2000-05-01 |      12.0 |      10.0 |       11.0 |  10.0 |   11.0 |
    | 2000-06-01 |       nan |      11.0 |       12.0 |  11.0 |   12.0 |
    | 2000-07-01 |       nan |      12.0 |       13.0 |  12.0 |   13.0 |
    | 2000-08-01 |       nan |       9.0 |        9.9 |   9.0 |    9.9 |
    | 2000-09-01 |       nan |       6.0 |        6.6 |   6.0 |    6.6 |
    | 2000-10-01 |       nan |       3.0 |        3.3 |   3.0 |    3.3 |

Deactivate the submodel
________________________

    If we deactivate the submodel, the simulated discharge does not get corrected
    at all:

    >>> model.outputcorrmodels[0].parameters.control.active(False)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        8.0 |   8.0 |    8.0 |
    | 2000-02-01 |      10.8 |       9.0 |        9.0 |   9.0 |    9.0 |
    | 2000-03-01 |      12.6 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-04-01 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-05-01 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-06-01 |       nan |      11.0 |       11.0 |  11.0 |   11.0 |
    | 2000-07-01 |       nan |      12.0 |       12.0 |  12.0 |   12.0 |
    | 2000-08-01 |       nan |       9.0 |        9.0 |   9.0 |    9.0 |
    | 2000-09-01 |       nan |       6.0 |        6.0 |   6.0 |    6.0 |
    | 2000-10-01 |       nan |       3.0 |        3.0 |   3.0 |    3.0 |

Use a longer evaluation window
______________________________

    We activate the submodel and increase the maximum shifts again:

    >>> model.outputcorrmodels[0].parameters.control.active(True)
    >>> model.outputcorrmodels[0].parameters.control.maxabsshift(100.0)
    >>> model.outputcorrmodels[0].parameters.control.maxrelshift(1.0)

    We set the evaluation window to three time steps and set `lowerlimit(12.0)`.
    Now the correction is only active if the mean of the last three observations
    is equal or greater than 12.0. For the first four time steps, this is not the
    case, so the simulated discharge does not get corrected.

    >>> model.outputcorrmodels[0].parameters.control.evaluationwindow(3.0)
    >>> model.outputcorrmodels[0].parameters.control.lowerlimit(12.0)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        8.0 |   8.0 |    8.0 |
    | 2000-02-01 |      10.8 |       9.0 |        9.0 |   9.0 |    9.0 |
    | 2000-03-01 |      12.6 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-04-01 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.0 |  11.0 |   13.0 |
    | 2000-07-01 |       nan |      12.0 |       14.0 |  12.0 |   14.0 |
    | 2000-08-01 |       nan |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-09-01 |       nan |       6.0 |        7.2 |   6.0 |    7.2 |
    | 2000-10-01 |       nan |       3.0 |        3.6 |   3.0 |    3.6 |

    If we set `correctionmode(option="forecast")`, the correction will only
    start after the fifth timestep:

    >>> model.outputcorrmodels[0].parameters.control.correctionmode(option="forecast")

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        8.0 |   8.0 |    8.0 |
    | 2000-02-01 |      10.8 |       9.0 |        9.0 |   9.0 |    9.0 |
    | 2000-03-01 |      12.6 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-04-01 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-05-01 |      12.0 |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-06-01 |       nan |      11.0 |       13.0 |  11.0 |   13.0 |
    | 2000-07-01 |       nan |      12.0 |       14.0 |  12.0 |   14.0 |
    | 2000-08-01 |       nan |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-09-01 |       nan |       6.0 |        7.2 |   6.0 |    7.2 |
    | 2000-10-01 |       nan |       3.0 |        3.6 |   3.0 |    3.6 |

Skipping NaN-Values
___________________

    When calculating the residual, NaN values can be skipped (up to |MaxNaNSkip|
    time steps). We demonstrate this by setting the last three observations in
    the historical period to `nan` and using `maxnanskip(3)`. We see that the last
    residual (`1.8`) is used because three steps without observations are skipped.

    >>> model.outputcorrmodels[0].parameters.control.evaluationwindow(1)
    >>> model.outputcorrmodels[0].parameters.control.lowerlimit(0.0)
    >>> model.outputcorrmodels[0].parameters.control.correctionmode(option="both")
    >>> with pub.options.checkseries(False):
    ...     model.sequences.inputs.discharge.series = [9.6, 10.8] + 8 * [nan]
    >>> model.outputcorrmodels[0].parameters.control.maxnanskip(3)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |       nan |      10.0 |       11.8 |  10.0 |   11.8 |
    | 2000-04-01 |       nan |      10.0 |       11.8 |  10.0 |   11.8 |
    | 2000-05-01 |       nan |      10.0 |       11.8 |  10.0 |   11.8 |
    | 2000-06-01 |       nan |      11.0 |       12.8 |  11.0 |   12.8 |
    | 2000-07-01 |       nan |      12.0 |       13.8 |  12.0 |   13.8 |
    | 2000-08-01 |       nan |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-09-01 |       nan |       6.0 |        7.2 |   6.0 |    7.2 |
    | 2000-10-01 |       nan |       3.0 |        3.6 |   3.0 |    3.6 |

    If we set `maxnanskip(2)`, after the fourth time step no residual can be
    calculated and the discharge will not be corrected:

    >>> model.outputcorrmodels[0].parameters.control.maxnanskip(2)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |       nan |      10.0 |       11.8 |  10.0 |   11.8 |
    | 2000-04-01 |       nan |      10.0 |       11.8 |  10.0 |   11.8 |
    | 2000-05-01 |       nan |      10.0 |       10.0 |  10.0 |   10.0 |
    | 2000-06-01 |       nan |      11.0 |       11.0 |  11.0 |   11.0 |
    | 2000-07-01 |       nan |      12.0 |       12.0 |  12.0 |   12.0 |
    | 2000-08-01 |       nan |       9.0 |        9.0 |   9.0 |    9.0 |
    | 2000-09-01 |       nan |       6.0 |        6.0 |   6.0 |    6.0 |
    | 2000-10-01 |       nan |       3.0 |        3.0 |   3.0 |    3.0 |


Use a mean value for the residual
_________________________________

    >>> with pub.options.checkseries(False):
    ...     model.sequences.inputs.discharge.series = (
    ...         [9.6, 10.8, 12.6, 12.0, 12.0] + 5 * [nan]
    ...     )

    Instead of using the last pointwise residual, it is possible to calculate a
    mean residual over the number of time steps set in `averagingwindow`. This only
    works in the forecast mode

    >>> model.outputcorrmodels[0].parameters.control.averagingwindow(3)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-04-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.2 |  11.0 |   13.2 |
    | 2000-07-01 |       nan |      12.0 |       14.2 |  12.0 |   14.2 |
    | 2000-08-01 |       nan |       9.0 |      10.98 |   9.0 |  10.98 |
    | 2000-09-01 |       nan |       6.0 |       7.32 |   6.0 |   7.32 |
    | 2000-10-01 |       nan |       3.0 |       3.66 |   3.0 |   3.66 |

    When using a mean value for the residual, it is possible to set the
    parameter `transition steps`. The correction will then change linearly from
    the last pointwise residual to the mean residual. This helps to avoid abrupt
    jumps between the last observation and the first forecast value:

    >>> model.outputcorrmodels[0].parameters.control.transitionsteps(4)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-04-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.0 |  11.0 |   13.0 |
    | 2000-07-01 |       nan |      12.0 |      14.05 |  12.0 |  14.05 |
    | 2000-08-01 |       nan |       9.0 |      10.89 |   9.0 |  10.89 |
    | 2000-09-01 |       nan |       6.0 |       7.29 |   6.0 |   7.29 |
    | 2000-10-01 |       nan |       3.0 |       3.66 |   3.0 |   3.66 |

Stationarity check
__________________

    So far, we had `stationaritycheck(False)`. With
    `stationaritycheck(window=4, ratiominmax=0.8)` we turn on a check for stationarity.
    That means, that if the ratio between minimum discharge and maximum discharge within
    the given period is lower than the given `ratiominmax`, it is assumed that
    the conditions are instationary. Then the correction in forecast mode is reduced
    linearly over the number of time steps set in `reductionsteps`.
    In our example, this ratio is `0.86`, so we set `ratiominmax(0.9)` to demonstrate
    the effect.

    >>> model.outputcorrmodels[0].parameters.control.transitionsteps(0)
    >>> model.outputcorrmodels[0].parameters.control.stationaritycheck(
    ...     active=True, window=4, ratiominmax=0.9
    ... )
    >>> model.outputcorrmodels[0].parameters.control.reductionsteps(4)

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-04-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.2 |  11.0 |   13.2 |
    | 2000-07-01 |       nan |      12.0 |      13.65 |  12.0 |  13.65 |
    | 2000-08-01 |       nan |       9.0 |       9.99 |   9.0 |   9.99 |
    | 2000-09-01 |       nan |       6.0 |       6.33 |   6.0 |   6.33 |
    | 2000-10-01 |       nan |       3.0 |        3.0 |   3.0 |    3.0 |

Variability check
_________________

    The optional variability check compares the sum of relative discharge changes
    with the keyword parameter `maxrelsumdelta`. If it is less, then the correction
    is based on the mean discharge over the timesteps set by the keyword parameter
    `averagingwindow`. In accordance with LARSIM, thicheck depends on stationary
    conditions, that's why it can be switched on by using two optional keyword
    parameters for the stationarity check. In the example, the sum of relative
    changes of the simulated discharge over the length of the `evaluationwindow`
    is `0.213`. Setting the keyword parameter `maxrelsumdelta` to `0.25` means that
    the variability check finds low variability, in this case the output correction
    will be based on the mean discharge over the averaging window set as a keyword
    parameter in `stationaritycheck` instead of the general averaging window.

    >>> control = model.outputcorrmodels[0].parameters.control
    >>> control.evaluationwindow(5)
    >>> control.stationaritycheck(
    ...     active=True, window=4, ratiominmax=0.8, maxrelsumdelta=0.25,
    ...     averagingwindow=4
    ... )

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-04-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.1 |  11.0 |   13.1 |
    | 2000-07-01 |       nan |      12.0 |       14.1 |  12.0 |   14.1 |
    | 2000-08-01 |       nan |       9.0 |      10.89 |   9.0 |  10.89 |
    | 2000-09-01 |       nan |       6.0 |       7.26 |   6.0 |   7.26 |
    | 2000-10-01 |       nan |       3.0 |       3.63 |   3.0 |   3.63 |

    If we change `maxrelsumdelta` to 0.2, the correction is based on the mean discharge
    over the general parameter `averagingwindow`:

    >>> control.stationaritycheck(
    ...     active=True, window=4, ratiominmax=0.8, maxrelsumdelta=0.2,
    ...     averagingwindow=4
    ... )

.. integration-test::

    >>> forecast_test("2000-01-06")
    |       date | discharge | originalq | correctedq | inlet | outlet |
    --------------------------------------------------------------------
    | 2000-01-01 |       9.6 |       8.0 |        9.6 |   8.0 |    9.6 |
    | 2000-02-01 |      10.8 |       9.0 |       10.8 |   9.0 |   10.8 |
    | 2000-03-01 |      12.6 |      10.0 |       12.6 |  10.0 |   12.6 |
    | 2000-04-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-05-01 |      12.0 |      10.0 |       12.0 |  10.0 |   12.0 |
    | 2000-06-01 |       nan |      11.0 |       13.2 |  11.0 |   13.2 |
    | 2000-07-01 |       nan |      12.0 |       14.2 |  12.0 |   14.2 |
    | 2000-08-01 |       nan |       9.0 |      10.98 |   9.0 |  10.98 |
    | 2000-09-01 |       nan |       6.0 |       7.32 |   6.0 |   7.32 |
    | 2000-10-01 |       nan |       3.0 |       3.66 |   3.0 |   3.66 |
"""

from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import statcorrinterfaces
from hydpy.models.statcorr import statcorr_model


class Model(statcorr_model.Sub_OutputCorrModel, statcorrinterfaces.OutputCorrModel_V1):
    """|statcorr_arima010.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="StatCorr-ARIMA010", description="ARIMA(0,1,0) output correction "
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
    ADD_METHODS = (
        statcorr_model.Calc_EvaluatedValue_V1,
        statcorr_model.Calc_IsActive_V1,
        statcorr_model.Calc_Residual_ResidualAnchor_V1,
        statcorr_model.Calc_Stationary_V1,
        statcorr_model.Calc_ReductionFactor_V1,
        statcorr_model.Calc_RelSumDelta_V1,
        statcorr_model.Calc_LowVariability_V1,
        statcorr_model.Calc_AveragedResidual_V1,
        statcorr_model.Calc_CorrectedValue_V1,
        statcorr_model.Update_ForecastStep_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
