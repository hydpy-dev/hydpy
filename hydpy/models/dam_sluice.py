# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Sluice version of HydPy-Dam.

|dam_sluice| is similar to |dam_pump| but is thought for modelling free flow through
sluices driven by differences between inner and outer water levels.  Principally, users
can define arbitrary relationships via |WaterLevelDifference2MaxFreeDischarge|,
including ones that allow for "negative outflow" so that |dam_sluice| takes water from
the downstream model.  However, be careful with that because, depending on the
downstream model's type and the current conditions, negative inflows can cause
problems.

Integration tests
=================

.. how_to_understand_integration_tests::

We take all of the following settings from the documentation on the application model
|dam_pump|:

>>> from hydpy import IntegrationTest, Element, Node, pub, round_
>>> pub.timegrids = "2000-01-01", "2000-01-21", "1d"

>>> from hydpy.aliases import dam_receivers_OWL, dam_receivers_RWL
>>> inflow = Node("inflow")
>>> outflow = Node("outflow")
>>> outer = Node("outer", variable=dam_receivers_OWL)
>>> remote = Node("remote", variable=dam_receivers_RWL)
>>> dam = Element("dam", inlets=inflow, outlets=outflow, receivers=(outer, remote))

>>> from hydpy.models.dam_sluice import *
>>> parameterstep()
>>> dam.model = model

>>> test = IntegrationTest(dam)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = factors.waterlevel, factors.outerwaterlevel, factors.remotewaterlevel
>>> test.inits = [(states.watervolume, 0.0),
...               (logs.loggedadjustedevaporation, 0.0),
...               (logs.loggedouterwaterlevel, 0.0),
...               (logs.loggedremotewaterlevel, 0.0)]
>>> test.reset_inits()
>>> conditions = model.conditions

>>> surfacearea(1.44)
>>> catchmentarea(86.4)
>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
>>> remotewaterlevelmaximumthreshold(2.0)
>>> remotewaterlevelmaximumtolerance(0.1)
>>> correctionprecipitation(1.0)
>>> correctionevaporation(1.0)
>>> weightevaporation(0.8)
>>> thresholdevaporation(0.0)
>>> toleranceevaporation(0.001)

>>> inputs.precipitation.series = 2.0
>>> inputs.evaporation.series = 1.0
>>> inflow.sequences.sim.series = 2.0
>>> outer.sequences.sim.series = 0.0
>>> remote.sequences.sim.series = numpy.linspace(0.0, 3.0, 20)

The remaining parameters are specific to |dam_sluice|.

We define a one-to-one relationship between the effective water level difference and
the highest possible free discharge values:

>>> waterleveldifference2maxfreedischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))

By setting the crest level to 1 m, only inner and outer water levels higher than one
meter are "effective" (can cause inflow or outflow through the hydraulic structure):

>>> crestlevel(1.0)
>>> crestleveltolerance(0.1)

The smoothing parameter |DischargeTolerance| is only relevant when the outflow must be
suppressed to not further increase to high water levels at a remote location (see
|Calc_FreeDischarge_V1|):

>>> dischargetolerance(0.1)

.. _dam_sluice_drainage:

drainage
________

The results of the following test run are pretty similar to those of the
:ref:`dam_pump_drainage` example.  Outflow starts again when the inner water level
reaches 1 m, which is the crest level in this example.  Afterwards, however, the
outflow increases approximately linearly with the further rising water level, but this
is more a (useful) difference in parameterisation than of the underlying equations.
The implemented flood protection mechanism suppresses the outflow quite similarly in
both examples:

.. integration-test::

    >>> test("dam_sluice_drainage")
    |   date | precipitation | evaporation | waterlevel | outerwaterlevel | remotewaterlevel | effectivewaterleveldifference | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxfreedischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           2.0 |         1.0 |   0.174816 |             0.0 |              0.0 |                           0.0 |              0.033333 |            0.013333 |              0.01 |    2.0 |           0.0 |              0.0 |      0.0 |    0.174816 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |           2.0 |         1.0 |   0.349114 |             0.0 |              0.0 |                      0.000001 |              0.033333 |               0.016 |             0.016 |    2.0 |      0.000001 |         0.000001 | 0.000001 |    0.349114 |    2.0 |   0.0 | 0.000001 | 0.157895 |
    | 03.01. |           2.0 |         1.0 |   0.523364 |             0.0 |         0.157895 |                      0.000019 |              0.033333 |            0.016533 |          0.016533 |    2.0 |       0.00001 |          0.00001 |  0.00001 |    0.523364 |    2.0 |   0.0 |  0.00001 | 0.315789 |
    | 04.01. |           2.0 |         1.0 |    0.69759 |             0.0 |         0.315789 |                      0.000354 |              0.033333 |             0.01664 |           0.01664 |    2.0 |      0.000186 |         0.000186 | 0.000186 |     0.69759 |    2.0 |   0.0 | 0.000186 | 0.473684 |
    | 05.01. |           2.0 |         1.0 |   0.871539 |             0.0 |         0.473684 |                      0.006403 |              0.033333 |            0.016661 |          0.016661 |    2.0 |      0.003379 |         0.003379 | 0.003379 |    0.871539 |    2.0 |   0.0 | 0.003379 | 0.631579 |
    | 06.01. |           2.0 |         1.0 |    1.04338 |             0.0 |         0.631579 |                      0.066021 |              0.033333 |            0.016666 |          0.016666 |    2.0 |      0.027762 |         0.027762 | 0.027762 |     1.04338 |    2.0 |   0.0 | 0.027762 | 0.789474 |
    | 07.01. |           2.0 |         1.0 |   1.206035 |             0.0 |         0.789474 |                      0.207323 |              0.033333 |            0.016666 |          0.016666 |    2.0 |      0.134092 |         0.134092 | 0.134092 |    1.206035 |    2.0 |   0.0 | 0.134092 | 0.947368 |
    | 08.01. |           2.0 |         1.0 |   1.355858 |             0.0 |         0.947368 |                      0.355783 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.282602 |         0.282602 | 0.282602 |    1.355858 |    2.0 |   0.0 | 0.282602 | 1.105263 |
    | 09.01. |           2.0 |         1.0 |   1.493327 |             0.0 |         1.105263 |                      0.493161 |              0.033333 |            0.016667 |          0.016667 |    2.0 |       0.42559 |          0.42559 |  0.42559 |    1.493327 |    2.0 |   0.0 |  0.42559 | 1.263158 |
    | 10.01. |           2.0 |         1.0 |   1.619421 |             0.0 |         1.263158 |                      0.619259 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.557245 |         0.557245 | 0.557245 |    1.619421 |    2.0 |   0.0 | 0.557245 | 1.421053 |
    | 11.01. |           2.0 |         1.0 |   1.735078 |             0.0 |         1.421053 |                      0.734928 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.678044 |         0.678044 | 0.678044 |    1.735078 |    2.0 |   0.0 | 0.678044 | 1.578947 |
    | 12.01. |           2.0 |         1.0 |   1.841162 |             0.0 |         1.578947 |                      0.841024 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.788848 |         0.788848 | 0.788848 |    1.841162 |    2.0 |   0.0 | 0.788848 | 1.736842 |
    | 13.01. |           2.0 |         1.0 |   1.938464 |             0.0 |         1.736842 |                      0.938338 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.890476 |         0.890481 | 0.890476 |    1.938464 |    2.0 |   0.0 | 0.890476 | 1.894737 |
    | 14.01. |           2.0 |         1.0 |   2.028354 |             0.0 |         1.894737 |                      1.028239 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.976279 |         0.984022 | 0.976279 |    2.028354 |    2.0 |   0.0 | 0.976279 | 2.052632 |
    | 15.01. |           2.0 |         1.0 |    2.19474 |             0.0 |         2.052632 |                      1.194738 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.090904 |         1.111644 | 0.090904 |     2.19474 |    2.0 |   0.0 | 0.090904 | 2.210526 |
    | 16.01. |           2.0 |         1.0 |   2.368973 |             0.0 |         2.210526 |                      1.368973 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.000081 |         1.281856 | 0.000081 |    2.368973 |    2.0 |   0.0 | 0.000081 | 2.368421 |
    | 17.01. |           2.0 |         1.0 |   2.543213 |             0.0 |         2.368421 |                      1.543213 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.456093 |      0.0 |    2.543213 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |           2.0 |         1.0 |   2.717453 |             0.0 |         2.526316 |                      1.717453 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.630333 |      0.0 |    2.717453 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |           2.0 |         1.0 |   2.891693 |             0.0 |         2.684211 |                      1.891693 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.804573 |      0.0 |    2.891693 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |           2.0 |         1.0 |   3.065933 |             0.0 |         2.842105 |                      2.065933 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.978813 |      0.0 |    3.065933 |    2.0 |   0.0 |      0.0 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_sluice_irrigation:

irrigation
__________

The flow through the hydraulic structure can be negative, corresponding to irrigation
instead land drainage.  We set the dam's "normal" inflow (from upstream areas) to 0 m³/s and
increase the outer water level to 2 m, which reverses the water level gradient:

>>> inflow.sequences.sim.series = 0.0
>>> outer.sequences.sim.series = 2.0

Now, the inner water level rises because of inflow from the area downstream.  The
remote water level still overshoots the threshold of 2 m, but this does not suppress
the inflow, as water losses should never increase flood risks:

.. integration-test::

    >>> test("dam_sluice_irrigation")
    |   date | precipitation | evaporation | waterlevel | outerwaterlevel | remotewaterlevel | effectivewaterleveldifference | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxfreedischarge |   outflow | watervolume | inflow | outer |   outflow |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           2.0 |         1.0 |   0.002016 |             0.0 |              0.0 |                           0.0 |              0.033333 |            0.013333 |              0.01 |    0.0 |           0.0 |              0.0 |       0.0 |    0.002016 |    0.0 |   2.0 |       0.0 |      0.0 |
    | 02.01. |           2.0 |         1.0 |   0.089914 |             2.0 |              0.0 |                          -1.0 |              0.033333 |               0.016 |          0.015999 |    0.0 |          -1.0 |             -1.0 |      -1.0 |    0.089914 |    0.0 |   2.0 |      -1.0 | 0.157895 |
    | 03.01. |           2.0 |         1.0 |   0.177765 |             2.0 |         0.157895 |                          -1.0 |              0.033333 |            0.016533 |          0.016533 |    0.0 |          -1.0 |             -1.0 |      -1.0 |    0.177765 |    0.0 |   2.0 |      -1.0 | 0.315789 |
    | 04.01. |           2.0 |         1.0 |   0.265607 |             2.0 |         0.315789 |                          -1.0 |              0.033333 |             0.01664 |           0.01664 |    0.0 |          -1.0 |             -1.0 |      -1.0 |    0.265607 |    0.0 |   2.0 |      -1.0 | 0.473684 |
    | 05.01. |           2.0 |         1.0 |   0.353448 |             2.0 |         0.473684 |                     -0.999999 |              0.033333 |            0.016661 |          0.016661 |    0.0 |     -0.999999 |        -0.999999 | -0.999999 |    0.353448 |    0.0 |   2.0 | -0.999999 | 0.631579 |
    | 06.01. |           2.0 |         1.0 |   0.441288 |             2.0 |         0.631579 |                     -0.999995 |              0.033333 |            0.016666 |          0.016666 |    0.0 |     -0.999997 |        -0.999997 | -0.999997 |    0.441288 |    0.0 |   2.0 | -0.999997 | 0.789474 |
    | 07.01. |           2.0 |         1.0 |   0.529127 |             2.0 |         0.789474 |                     -0.999979 |              0.033333 |            0.016666 |          0.016666 |    0.0 |     -0.999987 |        -0.999987 | -0.999987 |    0.529127 |    0.0 |   2.0 | -0.999987 | 0.947368 |
    | 08.01. |           2.0 |         1.0 |   0.616962 |             2.0 |         0.947368 |                     -0.999909 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.999944 |        -0.999944 | -0.999944 |    0.616962 |    0.0 |   2.0 | -0.999944 | 1.105263 |
    | 09.01. |           2.0 |         1.0 |   0.704781 |             2.0 |         1.105263 |                       -0.9996 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.999755 |        -0.999755 | -0.999755 |    0.704781 |    0.0 |   2.0 | -0.999755 | 1.263158 |
    | 10.01. |           2.0 |         1.0 |   0.792528 |             2.0 |         1.263158 |                     -0.998255 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.998928 |        -0.998928 | -0.998928 |    0.792528 |    0.0 |   2.0 | -0.998928 | 1.421053 |
    | 11.01. |           2.0 |         1.0 |   0.879976 |             2.0 |         1.421053 |                     -0.992676 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.995466 |        -0.995466 | -0.995466 |    0.879976 |    0.0 |   2.0 | -0.995466 | 1.578947 |
    | 12.01. |           2.0 |         1.0 |   0.966342 |             2.0 |         1.578947 |                     -0.973177 |              0.033333 |            0.016667 |          0.016667 |    0.0 |      -0.98294 |         -0.98294 |  -0.98294 |    0.966342 |    0.0 |   2.0 |  -0.98294 | 1.736842 |
    | 13.01. |           2.0 |         1.0 |   1.050159 |             2.0 |         1.736842 |                     -0.928947 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.953438 |        -0.953438 | -0.953438 |    1.050159 |    0.0 |   2.0 | -0.953438 | 1.894737 |
    | 14.01. |           2.0 |         1.0 |   1.129156 |             2.0 |         1.894737 |                      -0.86471 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.897644 |        -0.897644 | -0.897644 |    1.129156 |    0.0 |   2.0 | -0.897644 | 2.052632 |
    | 15.01. |           2.0 |         1.0 |   1.202321 |             2.0 |         2.052632 |                     -0.795899 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.830147 |        -0.830147 | -0.830147 |    1.202321 |    0.0 |   2.0 | -0.830147 | 2.210526 |
    | 16.01. |           2.0 |         1.0 |   1.269635 |             2.0 |         2.210526 |                     -0.729844 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.762441 |        -0.762441 | -0.762441 |    1.269635 |    0.0 |   2.0 | -0.762441 | 2.368421 |
    | 17.01. |           2.0 |         1.0 |    1.33144 |             2.0 |         2.368421 |                     -0.668425 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.698663 |        -0.698662 | -0.698663 |     1.33144 |    0.0 |   2.0 | -0.698663 | 2.526316 |
    | 18.01. |           2.0 |         1.0 |   1.388148 |             2.0 |         2.526316 |                     -0.611843 |              0.033333 |            0.016667 |          0.016667 |    0.0 |      -0.63968 |        -0.639679 |  -0.63968 |    1.388148 |    0.0 |   2.0 |  -0.63968 | 2.684211 |
    | 19.01. |           2.0 |         1.0 |    1.44017 |             2.0 |         2.684211 |                     -0.559863 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.585432 |        -0.585429 | -0.585432 |     1.44017 |    0.0 |   2.0 | -0.585432 | 2.842105 |
    | 20.01. |           2.0 |         1.0 |   1.487888 |             2.0 |         2.842105 |                     -0.512159 |              0.033333 |            0.016667 |          0.016667 |    0.0 |     -0.535627 |         -0.53562 | -0.535627 |    1.487888 |    0.0 |   2.0 | -0.535627 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_sluice_mixed:

mixed
_____

Finally, we reset the "normal" inflow to 2 m³/s but leave the outer water level at 2 m:

>>> inflow.sequences.sim.series = 2.0

This setting results in a "mixed" situation where initial inflow from downstream turns
into outflow as soon as the inner water level exceeds the outer one:

.. integration-test::

    >>> test("dam_sluice_mixed")
    |   date | precipitation | evaporation | waterlevel | outerwaterlevel | remotewaterlevel | effectivewaterleveldifference | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxfreedischarge |   outflow | watervolume | inflow | outer |   outflow |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           2.0 |         1.0 |   0.174816 |             0.0 |              0.0 |                           0.0 |              0.033333 |            0.013333 |              0.01 |    2.0 |           0.0 |              0.0 |       0.0 |    0.174816 |    2.0 |   2.0 |       0.0 |      0.0 |
    | 02.01. |           2.0 |         1.0 |   0.435513 |             2.0 |              0.0 |                     -0.999996 |              0.033333 |               0.016 |             0.016 |    2.0 |     -0.999998 |        -0.999998 | -0.999998 |    0.435513 |    2.0 |   2.0 | -0.999998 | 0.157895 |
    | 03.01. |           2.0 |         1.0 |    0.69615 |             2.0 |         0.157895 |                     -0.999654 |              0.033333 |            0.016533 |          0.016533 |    2.0 |     -0.999825 |        -0.999825 | -0.999825 |     0.69615 |    2.0 |   2.0 | -0.999825 | 0.315789 |
    | 04.01. |           2.0 |         1.0 |   0.956282 |             2.0 |         0.315789 |                     -0.977088 |              0.033333 |             0.01664 |           0.01664 |    2.0 |     -0.994092 |        -0.994092 | -0.994092 |    0.956282 |    2.0 |   2.0 | -0.994092 | 0.473684 |
    | 05.01. |           2.0 |         1.0 |   1.207986 |             2.0 |         0.473684 |                     -0.790236 |              0.033333 |            0.016661 |          0.016661 |    2.0 |     -0.896567 |        -0.896567 | -0.896567 |    1.207986 |    2.0 |   2.0 | -0.896567 | 0.631579 |
    | 06.01. |           2.0 |         1.0 |   1.440439 |             2.0 |         0.631579 |                     -0.559863 |              0.033333 |            0.016666 |          0.016666 |    2.0 |     -0.673771 |        -0.673771 | -0.673771 |    1.440439 |    2.0 |   2.0 | -0.673771 | 0.789474 |
    | 07.01. |           2.0 |         1.0 |   1.653686 |             2.0 |         0.789474 |                     -0.346591 |              0.033333 |            0.016666 |          0.016666 |    2.0 |     -0.451464 |        -0.451464 | -0.451464 |    1.653686 |    2.0 |   2.0 | -0.451464 | 0.947368 |
    | 08.01. |           2.0 |         1.0 |   1.849282 |             2.0 |         0.947368 |                     -0.150972 |              0.033333 |            0.016667 |          0.016667 |    2.0 |     -0.247173 |        -0.247173 | -0.247173 |    1.849282 |    2.0 |   2.0 | -0.247173 | 1.105263 |
    | 09.01. |           2.0 |         1.0 |   2.028687 |             2.0 |         1.105263 |                      0.028454 |              0.033333 |            0.016667 |          0.016667 |    2.0 |     -0.059784 |        -0.059784 | -0.059784 |    2.028687 |    2.0 |   2.0 | -0.059784 | 1.263158 |
    | 10.01. |           2.0 |         1.0 |   2.193242 |             2.0 |         1.263158 |                      0.193028 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.112094 |         0.112094 |  0.112094 |    2.193242 |    2.0 |   2.0 |  0.112094 | 1.421053 |
    | 11.01. |           2.0 |         1.0 |   2.344176 |             2.0 |         1.421053 |                       0.34398 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.269745 |         0.269745 |  0.269745 |    2.344176 |    2.0 |   2.0 |  0.269745 | 1.578947 |
    | 12.01. |           2.0 |         1.0 |   2.482617 |             2.0 |         1.578947 |                      0.482437 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.414347 |         0.414347 |  0.414347 |    2.482617 |    2.0 |   2.0 |  0.414347 | 1.736842 |
    | 13.01. |           2.0 |         1.0 |   2.609598 |             2.0 |         1.736842 |                      0.609433 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.546976 |         0.546979 |  0.546976 |    2.609598 |    2.0 |   2.0 |  0.546976 | 1.894737 |
    | 14.01. |           2.0 |         1.0 |   2.726504 |             2.0 |         1.894737 |                      0.726355 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.663585 |         0.668848 |  0.663585 |    2.726504 |    2.0 |   2.0 |  0.663585 | 2.052632 |
    | 15.01. |           2.0 |         1.0 |   2.895015 |             2.0 |         2.052632 |                      0.895014 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.066307 |         0.810858 |  0.066307 |    2.895015 |    2.0 |   2.0 |  0.066307 | 2.210526 |
    | 16.01. |           2.0 |         1.0 |    3.06925 |             2.0 |         2.210526 |                       1.06925 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.000062 |         0.982133 |  0.000062 |     3.06925 |    2.0 |   2.0 |  0.000062 | 2.368421 |
    | 17.01. |           2.0 |         1.0 |    3.24349 |             2.0 |         2.368421 |                       1.24349 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.15637 |       0.0 |     3.24349 |    2.0 |   2.0 |       0.0 | 2.526316 |
    | 18.01. |           2.0 |         1.0 |    3.41773 |             2.0 |         2.526316 |                       1.41773 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.33061 |       0.0 |     3.41773 |    2.0 |   2.0 |       0.0 | 2.684211 |
    | 19.01. |           2.0 |         1.0 |    3.59197 |             2.0 |         2.684211 |                       1.59197 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.50485 |       0.0 |     3.59197 |    2.0 |   2.0 |       0.0 | 2.842105 |
    | 20.01. |           2.0 |         1.0 |    3.76621 |             2.0 |         2.842105 |                       1.76621 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.67909 |       0.0 |     3.76621 |    2.0 |   2.0 |       0.0 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
import hydpy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import

from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core.typingtools import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(modeltools.ELSModel):
    """Sluice version of HydPy-Dam."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (dam_model.Calc_AdjustedEvaporation_V1,)
    RECEIVER_METHODS = (
        dam_model.Pick_LoggedOuterWaterLevel_V1,
        dam_model.Pick_LoggedRemoteWaterLevel_V1,
    )
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_OuterWaterLevel_V1,
        dam_model.Calc_RemoteWaterLevel_V1,
        dam_model.Calc_EffectiveWaterLevelDifference_V1,
        dam_model.Calc_MaxFreeDischarge_V1,
        dam_model.Calc_FreeDischarge_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_Outflow_V4,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V1,)
    OUTLET_METHODS = (
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_OuterWaterLevel_V1,
        dam_model.Calc_RemoteWaterLevel_V1,
        dam_model.Pass_Outflow_V1,
    )
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    def check_waterbalance(self, initial_conditions: ConditionsModel) -> float:
        r"""Determine the water balance error of the previous simulation run in million
        m³.

        Method |Model.check_waterbalance| calculates the balance error as follows:

        :math:`Seconds \cdot 10^{-6} \cdot \sum_{t=t0}^{t1}
        \big( AdjustedPrecipitation_t - ActualEvaporation_t + Inflow_t - Outflow_t \big)
        + \big( WaterVolume_{t0}^k - WaterVolume_{t1}^k \big)`

        The returned error should always be in scale with numerical precision so
        that it does not affect the simulation results in any relevant manner.

        Pick the required initial conditions before starting the simulation run via
        property |Sequences.conditions|.  See the integration tests of the application
        model |dam_v008| for some examples.
        """
        fluxes = self.sequences.fluxes
        first = initial_conditions["model"]["states"]
        last = self.sequences.states
        return (hydpy.pub.timegrids.stepsize.seconds / 1e6) * (
            sum(fluxes.adjustedprecipitation.series)
            - sum(fluxes.actualevaporation.series)
            + sum(fluxes.inflow.series)
            - sum(fluxes.outflow.series)
        ) - (last.watervolume - first["watervolume"])


tester = Tester()
cythonizer = Cythonizer()
