# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Pumping station combined with a sluice.

|dam_pump_sluice| combines the "forced discharge" component of |dam_pump| with the
"free discharge" component of |dam_sluice|.

Integration tests
=================

.. how_to_understand_integration_tests::

We take all of the following settings from the documentation on the application models
|dam_pump| and |dam_sluice|:

>>> from hydpy import IntegrationTest, Element, Node, pub, round_
>>> pub.timegrids = "2000-01-01", "2000-01-21", "1d"

>>> from hydpy.aliases import dam_receivers_OWL, dam_receivers_RWL
>>> inflow = Node("inflow")
>>> outflow = Node("outflow")
>>> outer = Node("outer", variable=dam_receivers_OWL)
>>> remote = Node("remote", variable=dam_receivers_RWL)
>>> dam = Element("dam", inlets=inflow, outlets=outflow, receivers=(outer, remote))

>>> from hydpy.models.dam_pump_sluice import *
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
>>> conditions = sequences.conditions

>>> surfacearea(1.44)
>>> catchmentarea(86.4)
>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
>>> waterlevelmaximumthreshold(1.0)
>>> waterlevelmaximumtolerance(0.1)
>>> remotewaterlevelmaximumthreshold(2.0)
>>> remotewaterlevelmaximumtolerance(0.1)
>>> crestlevel(1.0)
>>> crestleveltolerance(0.1)
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


.. _dam_pump_sluice_pump_only:

pump only
_________

First, we demonstrate the proper implementation of the "forced discharge" components by
enabling them, like in the :ref:`dam_pump_drainage` example of application model
|dam_pump|, while turning off the "free discharge" component:

>>> waterleveldifference2maxforceddischarge(PPoly.from_data(xs=[0.0], ys=[1.0]))
>>> waterleveldifference2maxfreedischarge(PPoly.from_data(xs=[0.0], ys=[0.0]))

To reproduce the results of |dam_pump| exactly, we must set |DischargeTolerance| to
zero (see the critical remark at the end of the documentation on method
|Calc_FreeDischarge_V1|):

>>> dischargetolerance(0.0)

The following results are identical to those of the :ref:`dam_pump_drainage` example:

.. integration-test::

    >>> test("dam_pump_sluice_pump_only")
    |   date | precipitation | evaporation | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | effectivewaterleveldifference | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxforceddischarge | maxfreedischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           2.0 |         1.0 |   0.174816 |             0.0 |              0.0 |             0.175104 |                           0.0 |              0.033333 |            0.013333 |              0.01 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.174816 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |           2.0 |         1.0 |   0.349114 |             0.0 |              0.0 |             0.349114 |                      0.000001 |              0.033333 |               0.016 |             0.016 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.349114 |    2.0 |   0.0 |      0.0 | 0.157895 |
    | 03.01. |           2.0 |         1.0 |   0.523365 |             0.0 |         0.157895 |             0.523365 |                      0.000019 |              0.033333 |            0.016533 |          0.016533 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.523365 |    2.0 |   0.0 |      0.0 | 0.315789 |
    | 04.01. |           2.0 |         1.0 |   0.697607 |             0.0 |         0.315789 |             0.697607 |                      0.000354 |              0.033333 |             0.01664 |           0.01664 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.697607 |    2.0 |   0.0 |      0.0 | 0.473684 |
    | 05.01. |           2.0 |         1.0 |   0.871728 |             0.0 |         0.473684 |             0.871848 |                      0.006408 |              0.033333 |            0.016661 |          0.016661 |    2.0 |           0.0 |                1.0 |              0.0 |        0.001382 | 0.001382 |    0.871728 |    2.0 |   0.0 | 0.001382 | 0.631579 |
    | 06.01. |           2.0 |         1.0 |   1.025317 |             0.0 |         0.631579 |             1.025227 |                      0.054931 |              0.033333 |            0.016666 |          0.016666 |    2.0 |           0.0 |                1.0 |              0.0 |        0.239024 | 0.239024 |    1.025317 |    2.0 |   0.0 | 0.239024 | 0.789474 |
    | 07.01. |           2.0 |         1.0 |   1.118209 |             0.0 |         0.789474 |             1.118263 |                      0.125766 |              0.033333 |            0.016666 |          0.016666 |    2.0 |           0.0 |                1.0 |              0.0 |        0.941528 | 0.941528 |    1.118209 |    2.0 |   0.0 | 0.941528 | 0.947368 |
    | 08.01. |           2.0 |         1.0 |    1.20624 |             0.0 |         0.947368 |             1.206425 |                      0.208199 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.997784 | 0.997784 |     1.20624 |    2.0 |   0.0 | 0.997784 | 1.105263 |
    | 09.01. |           2.0 |         1.0 |   1.294084 |             0.0 |         1.105263 |             1.294087 |                      0.294494 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.999961 | 0.999961 |    1.294084 |    2.0 |   0.0 | 0.999961 | 1.263158 |
    | 10.01. |           2.0 |         1.0 |   1.381924 |             0.0 |         1.263158 |             1.381924 |                      0.382016 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.999999 | 0.999999 |    1.381924 |    2.0 |   0.0 | 0.999999 | 1.421053 |
    | 11.01. |           2.0 |         1.0 |   1.469764 |             0.0 |         1.421053 |             1.469764 |                      0.469785 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             1.0 |      1.0 |    1.469764 |    2.0 |   0.0 |      1.0 | 1.578947 |
    | 12.01. |           2.0 |         1.0 |   1.557604 |             0.0 |         1.578947 |             1.557604 |                      0.557609 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             1.0 |      1.0 |    1.557604 |    2.0 |   0.0 |      1.0 | 1.736842 |
    | 13.01. |           2.0 |         1.0 |   1.645444 |             0.0 |         1.736842 |             1.645444 |                      0.645445 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.999994 | 0.999994 |    1.645444 |    2.0 |   0.0 | 0.999994 | 1.894737 |
    | 14.01. |           2.0 |         1.0 |   1.733964 |             0.0 |         1.894737 |             1.733964 |                      0.733964 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.992131 | 0.992131 |    1.733964 |    2.0 |   0.0 | 0.992131 | 2.052632 |
    | 15.01. |           2.0 |         1.0 |   1.901139 |             0.0 |         2.052632 |             1.901139 |                      0.901139 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.081774 | 0.081774 |    1.901139 |    2.0 |   0.0 | 0.081774 | 2.210526 |
    | 16.01. |           2.0 |         1.0 |   2.075373 |             0.0 |         2.210526 |             2.075373 |                      1.075373 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.000063 | 0.000063 |    2.075373 |    2.0 |   0.0 | 0.000063 | 2.368421 |
    | 17.01. |           2.0 |         1.0 |   2.249613 |             0.0 |         2.368421 |             2.249613 |                      1.249613 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.249613 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |           2.0 |         1.0 |   2.423853 |             0.0 |         2.526316 |             2.423853 |                      1.423853 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.423853 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |           2.0 |         1.0 |   2.598093 |             0.0 |         2.684211 |             2.598093 |                      1.598093 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.598093 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |           2.0 |         1.0 |   2.772333 |             0.0 |         2.842105 |             2.772333 |                      1.772333 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.772333 |    2.0 |   0.0 |      0.0 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_pump_sluice_sluice_only:

sluice only
___________

Next, we switch from pure "forced discharge" to pure "free discharge" according to the
:ref:`dam_sluice_drainage` example on application model |dam_sluice|:

>>> waterleveldifference2maxforceddischarge(PPoly.from_data(xs=[0.0], ys=[0.0]))
>>> waterleveldifference2maxfreedischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
>>> dischargetolerance(0.1)

The following results are identical to those of the :ref:`dam_sluice_drainage` example:

.. integration-test::

    >>> test("dam_pump_sluice_sluice_only")
    |   date | precipitation | evaporation | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | effectivewaterleveldifference | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxforceddischarge | maxfreedischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           2.0 |         1.0 |   0.174816 |             0.0 |              0.0 |             0.175104 |                           0.0 |              0.033333 |            0.013333 |              0.01 |    2.0 |           0.0 |                0.0 |              0.0 |             0.0 |      0.0 |    0.174816 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |           2.0 |         1.0 |   0.349114 |             0.0 |              0.0 |             0.349114 |                      0.000001 |              0.033333 |               0.016 |             0.016 |    2.0 |      0.000001 |                0.0 |         0.000001 |             0.0 | 0.000001 |    0.349114 |    2.0 |   0.0 | 0.000001 | 0.157895 |
    | 03.01. |           2.0 |         1.0 |   0.523364 |             0.0 |         0.157895 |             0.523365 |                      0.000019 |              0.033333 |            0.016533 |          0.016533 |    2.0 |       0.00001 |                0.0 |          0.00001 |             0.0 |  0.00001 |    0.523364 |    2.0 |   0.0 |  0.00001 | 0.315789 |
    | 04.01. |           2.0 |         1.0 |    0.69759 |             0.0 |         0.315789 |             0.697605 |                      0.000354 |              0.033333 |             0.01664 |           0.01664 |    2.0 |      0.000186 |                0.0 |         0.000186 |             0.0 | 0.000186 |     0.69759 |    2.0 |   0.0 | 0.000186 | 0.473684 |
    | 05.01. |           2.0 |         1.0 |   0.871539 |             0.0 |         0.473684 |               0.8718 |                      0.006403 |              0.033333 |            0.016661 |          0.016661 |    2.0 |      0.003379 |                0.0 |         0.003379 |             0.0 | 0.003379 |    0.871539 |    2.0 |   0.0 | 0.003379 | 0.631579 |
    | 06.01. |           2.0 |         1.0 |    1.04338 |             0.0 |         0.631579 |             1.042574 |                      0.066021 |              0.033333 |            0.016666 |          0.016666 |    2.0 |      0.027762 |                0.0 |         0.027762 |             0.0 | 0.027762 |     1.04338 |    2.0 |   0.0 | 0.027762 | 0.789474 |
    | 07.01. |           2.0 |         1.0 |   1.206035 |             0.0 |         0.789474 |             1.205522 |                      0.207323 |              0.033333 |            0.016666 |          0.016666 |    2.0 |      0.134092 |                0.0 |         0.134092 |             0.0 | 0.134092 |    1.206035 |    2.0 |   0.0 | 0.134092 | 0.947368 |
    | 08.01. |           2.0 |         1.0 |   1.355858 |             0.0 |         0.947368 |             1.355639 |                      0.355783 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.282602 |                0.0 |         0.282602 |             0.0 | 0.282602 |    1.355858 |    2.0 |   0.0 | 0.282602 | 1.105263 |
    | 09.01. |           2.0 |         1.0 |   1.493327 |             0.0 |         1.105263 |             1.493147 |                      0.493161 |              0.033333 |            0.016667 |          0.016667 |    2.0 |       0.42559 |                0.0 |          0.42559 |             0.0 |  0.42559 |    1.493327 |    2.0 |   0.0 |  0.42559 | 1.263158 |
    | 10.01. |           2.0 |         1.0 |   1.619421 |             0.0 |         1.263158 |             1.619257 |                      0.619259 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.557245 |                0.0 |         0.557245 |             0.0 | 0.557245 |    1.619421 |    2.0 |   0.0 | 0.557245 | 1.421053 |
    | 11.01. |           2.0 |         1.0 |   1.735078 |             0.0 |         1.421053 |             1.734928 |                      0.734928 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.678044 |                0.0 |         0.678044 |             0.0 | 0.678044 |    1.735078 |    2.0 |   0.0 | 0.678044 | 1.578947 |
    | 12.01. |           2.0 |         1.0 |   1.841162 |             0.0 |         1.578947 |             1.841024 |                      0.841024 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.788848 |                0.0 |         0.788848 |             0.0 | 0.788848 |    1.841162 |    2.0 |   0.0 | 0.788848 | 1.736842 |
    | 13.01. |           2.0 |         1.0 |   1.938464 |             0.0 |         1.736842 |             1.938338 |                      0.938338 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.890476 |                0.0 |         0.890481 |             0.0 | 0.890476 |    1.938464 |    2.0 |   0.0 | 0.890476 | 1.894737 |
    | 14.01. |           2.0 |         1.0 |   2.028354 |             0.0 |         1.894737 |             2.028239 |                      1.028239 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.976279 |                0.0 |         0.984022 |             0.0 | 0.976279 |    2.028354 |    2.0 |   0.0 | 0.976279 | 2.052632 |
    | 15.01. |           2.0 |         1.0 |    2.19474 |             0.0 |         2.052632 |             2.194738 |                      1.194738 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.090904 |                0.0 |         1.111644 |             0.0 | 0.090904 |     2.19474 |    2.0 |   0.0 | 0.090904 | 2.210526 |
    | 16.01. |           2.0 |         1.0 |   2.368973 |             0.0 |         2.210526 |             2.368973 |                      1.368973 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.000081 |                0.0 |         1.281856 |             0.0 | 0.000081 |    2.368973 |    2.0 |   0.0 | 0.000081 | 2.368421 |
    | 17.01. |           2.0 |         1.0 |   2.543213 |             0.0 |         2.368421 |             2.543213 |                      1.543213 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.456093 |             0.0 |      0.0 |    2.543213 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |           2.0 |         1.0 |   2.717453 |             0.0 |         2.526316 |             2.717453 |                      1.717453 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.630333 |             0.0 |      0.0 |    2.717453 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |           2.0 |         1.0 |   2.891693 |             0.0 |         2.684211 |             2.891693 |                      1.891693 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.804573 |             0.0 |      0.0 |    2.891693 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |           2.0 |         1.0 |   3.065933 |             0.0 |         2.842105 |             3.065933 |                      2.065933 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.978813 |             0.0 |      0.0 |    3.065933 |    2.0 |   0.0 |      0.0 |      3.0 |

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_pump_sluice_pump_and_sluice:

pump and sluice
_______________

The last example shows how |dam_pump_sluice| calculates both discharge types
simultaneously:

.. integration-test::

    >>> waterleveldifference2maxforceddischarge(PPoly.from_data(xs=[0.0], ys=[1.0]))
    >>> test("dam_pump_sluice_pump_and_sluice")
    |   date | precipitation | evaporation | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | effectivewaterleveldifference | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxforceddischarge | maxfreedischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           2.0 |         1.0 |   0.174816 |             0.0 |              0.0 |             0.175104 |                           0.0 |              0.033333 |            0.013333 |              0.01 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.174816 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |           2.0 |         1.0 |   0.349114 |             0.0 |              0.0 |             0.349114 |                      0.000001 |              0.033333 |               0.016 |             0.016 |    2.0 |      0.000001 |                1.0 |         0.000001 |             0.0 | 0.000001 |    0.349114 |    2.0 |   0.0 | 0.000001 | 0.157895 |
    | 03.01. |           2.0 |         1.0 |   0.523364 |             0.0 |         0.157895 |             0.523365 |                      0.000019 |              0.033333 |            0.016533 |          0.016533 |    2.0 |       0.00001 |                1.0 |          0.00001 |             0.0 |  0.00001 |    0.523364 |    2.0 |   0.0 |  0.00001 | 0.315789 |
    | 04.01. |           2.0 |         1.0 |    0.69759 |             0.0 |         0.315789 |             0.697605 |                      0.000354 |              0.033333 |             0.01664 |           0.01664 |    2.0 |      0.000186 |                1.0 |         0.000186 |             0.0 | 0.000187 |     0.69759 |    2.0 |   0.0 | 0.000187 | 0.473684 |
    | 05.01. |           2.0 |         1.0 |    0.87142 |             0.0 |         0.473684 |               0.8718 |                      0.006403 |              0.033333 |            0.016661 |          0.016661 |    2.0 |      0.003379 |                1.0 |         0.003379 |        0.001379 | 0.004757 |     0.87142 |    2.0 |   0.0 | 0.004757 | 0.631579 |
    | 06.01. |           2.0 |         1.0 |   1.023399 |             0.0 |         0.631579 |             1.023166 |                      0.053693 |              0.033333 |            0.016666 |          0.016666 |    2.0 |      0.025763 |                1.0 |         0.025763 |         0.23189 | 0.257653 |    1.023399 |    2.0 |   0.0 | 0.257653 | 0.789474 |
    | 07.01. |           2.0 |         1.0 |   1.109569 |             0.0 |         0.789474 |             1.109393 |                      0.118026 |              0.033333 |            0.016666 |          0.016666 |    2.0 |      0.085711 |                1.0 |         0.085711 |        0.933614 | 1.019324 |    1.109569 |    2.0 |   0.0 | 1.019324 | 0.947368 |
    | 08.01. |           2.0 |         1.0 |   1.184393 |             0.0 |         0.947368 |             1.184375 |                      0.186934 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.152506 |                1.0 |         0.152506 |         0.99814 | 1.150647 |    1.184393 |    2.0 |   0.0 | 1.150647 | 1.105263 |
    | 09.01. |           2.0 |         1.0 |   1.253166 |             0.0 |         1.105263 |             1.253069 |                      0.253882 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.220749 |                1.0 |         0.220749 |        0.999936 | 1.220685 |    1.253166 |    2.0 |   0.0 | 1.220685 | 1.263158 |
    | 10.01. |           2.0 |         1.0 |   1.316324 |             0.0 |         1.263158 |             1.316239 |                       0.31652 |              0.033333 |            0.016667 |          0.016667 |    2.0 |       0.28567 |                1.0 |          0.28567 |        0.999997 | 1.285667 |    1.316324 |    2.0 |   0.0 | 1.285667 | 1.421053 |
    | 11.01. |           2.0 |         1.0 |   1.374281 |             0.0 |         1.421053 |             1.374205 |                       0.37431 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.345876 |                1.0 |         0.345876 |             1.0 | 1.345876 |    1.374281 |    2.0 |   0.0 | 1.345876 | 1.578947 |
    | 12.01. |           2.0 |         1.0 |   1.427449 |             0.0 |         1.578947 |             1.427379 |                      0.427422 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.401298 |                1.0 |         0.401298 |             1.0 | 1.401298 |    1.427449 |    2.0 |   0.0 | 1.401298 | 1.736842 |
    | 13.01. |           2.0 |         1.0 |   1.476219 |             0.0 |         1.736842 |             1.476156 |                      0.476175 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.452195 |                1.0 |         0.452198 |        0.999994 | 1.452189 |    1.476219 |    2.0 |   0.0 | 1.452189 | 1.894737 |
    | 14.01. |           2.0 |         1.0 |   1.521931 |             0.0 |         1.894737 |             1.521872 |                      0.521881 |              0.033333 |            0.016667 |          0.016667 |    2.0 |       0.49547 |                1.0 |         0.499399 |        0.992131 | 1.487601 |    1.521931 |    2.0 |   0.0 | 1.487601 | 2.052632 |
    | 15.01. |           2.0 |         1.0 |   1.684842 |             0.0 |         2.052632 |             1.684841 |                      0.684841 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.049347 |                1.0 |         0.603485 |        0.081774 | 0.131121 |    1.684842 |    2.0 |   0.0 | 0.131121 | 2.210526 |
    | 16.01. |           2.0 |         1.0 |   1.859072 |             0.0 |         2.210526 |             1.859072 |                      0.859072 |              0.033333 |            0.016667 |          0.016667 |    2.0 |      0.000048 |                1.0 |         0.771957 |        0.000063 | 0.000111 |    1.859072 |    2.0 |   0.0 | 0.000111 | 2.368421 |
    | 17.01. |           2.0 |         1.0 |   2.033312 |             0.0 |         2.368421 |             2.033312 |                      1.033312 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         0.946192 |             0.0 |      0.0 |    2.033312 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |           2.0 |         1.0 |   2.207552 |             0.0 |         2.526316 |             2.207552 |                      1.207552 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         1.120432 |             0.0 |      0.0 |    2.207552 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |           2.0 |         1.0 |   2.381792 |             0.0 |         2.684211 |             2.381792 |                      1.381792 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         1.294672 |             0.0 |      0.0 |    2.381792 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |           2.0 |         1.0 |   2.556032 |             0.0 |         2.842105 |             2.556032 |                      1.556032 |              0.033333 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         1.468912 |             0.0 |      0.0 |    2.556032 |    2.0 |   0.0 |      0.0 |      3.0 |

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
    """Pumping station combined with a sluice."""

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
        dam_model.Calc_WaterLevelDifference_V1,
        dam_model.Calc_EffectiveWaterLevelDifference_V1,
        dam_model.Calc_MaxForcedDischarge_V1,
        dam_model.Calc_MaxFreeDischarge_V1,
        dam_model.Calc_ForcedDischarge_V1,
        dam_model.Calc_FreeDischarge_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_Outflow_V5,
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

    def check_waterbalance(
        self,
        initial_conditions: Dict[str, Dict[str, ArrayFloat]],
    ) -> float:
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
        first = initial_conditions["states"]
        last = self.sequences.states
        return (hydpy.pub.timegrids.stepsize.seconds / 1e6) * (
            sum(fluxes.adjustedprecipitation.series)
            - sum(fluxes.actualevaporation.series)
            + sum(fluxes.inflow.series)
            - sum(fluxes.outflow.series)
        ) - (last.watervolume - first["watervolume"])


tester = Tester()
cythonizer = Cythonizer()
