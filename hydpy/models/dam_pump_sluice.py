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

>>> with model.add_precipmodel_v2("meteo_precip_io"):
...     precipitationfactor(1.0)
>>> with model.add_pemodel_v1("evap_io"):
...     evapotranspirationfactor(1.0)

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

>>> model.precipmodel.sequences.inputs.precipitation.series = 2.0
>>> model.pemodel.sequences.inputs.referenceevapotranspiration.series = 1.0
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
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | effectivewaterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxforceddischarge | maxfreedischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.174533 |             0.0 |              0.0 |             0.174533 |                           0.0 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.013278 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.174533 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |    0.34883 |             0.0 |              0.0 |              0.34883 |                      0.000001 |           2.0 |              0.033333 |                  1.0 |               0.016 |             0.016 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |     0.34883 |    2.0 |   0.0 |      0.0 | 0.157895 |
    | 03.01. |   0.523082 |             0.0 |         0.157895 |             0.523082 |                      0.000019 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.523082 |    2.0 |   0.0 |      0.0 | 0.315789 |
    | 04.01. |   0.697324 |             0.0 |         0.315789 |             0.697324 |                      0.000353 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.697324 |    2.0 |   0.0 |      0.0 | 0.473684 |
    | 05.01. |   0.871535 |             0.0 |         0.473684 |             0.871534 |                      0.006376 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    2.0 |           0.0 |                1.0 |              0.0 |        0.000342 | 0.000342 |    0.871535 |    2.0 |   0.0 | 0.000342 | 0.631579 |
    | 06.01. |   1.025268 |             0.0 |         0.631579 |             1.025276 |                      0.054961 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |           0.0 |                1.0 |              0.0 |        0.237348 | 0.237348 |    1.025268 |    2.0 |   0.0 | 0.237348 | 0.789474 |
    | 07.01. |   1.118228 |             0.0 |         0.789474 |             1.118229 |                      0.125736 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |           0.0 |                1.0 |              0.0 |         0.94074 |  0.94074 |    1.118228 |    2.0 |   0.0 |  0.94074 | 0.947368 |
    | 08.01. |    1.20616 |             0.0 |         0.947368 |             1.206165 |                      0.207947 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.998939 | 0.998939 |     1.20616 |    2.0 |   0.0 | 0.998939 | 1.105263 |
    | 09.01. |   1.294004 |             0.0 |         1.105263 |             1.294007 |                      0.294415 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.999961 | 0.999961 |    1.294004 |    2.0 |   0.0 | 0.999961 | 1.263158 |
    | 10.01. |   1.381844 |             0.0 |         1.263158 |             1.381844 |                      0.381936 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.999999 | 0.999999 |    1.381844 |    2.0 |   0.0 | 0.999999 | 1.421053 |
    | 11.01. |   1.469684 |             0.0 |         1.421053 |             1.469684 |                      0.469705 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             1.0 |      1.0 |    1.469684 |    2.0 |   0.0 |      1.0 | 1.578947 |
    | 12.01. |   1.557524 |             0.0 |         1.578947 |             1.557524 |                      0.557528 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             1.0 |      1.0 |    1.557524 |    2.0 |   0.0 |      1.0 | 1.736842 |
    | 13.01. |   1.645364 |             0.0 |         1.736842 |             1.645364 |                      0.645365 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.999994 | 0.999994 |    1.645364 |    2.0 |   0.0 | 0.999994 | 1.894737 |
    | 14.01. |   1.733884 |             0.0 |         1.894737 |             1.733884 |                      0.733884 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.992131 | 0.992131 |    1.733884 |    2.0 |   0.0 | 0.992131 | 2.052632 |
    | 15.01. |   1.901059 |             0.0 |         2.052632 |             1.901059 |                      0.901059 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.081774 | 0.081774 |    1.901059 |    2.0 |   0.0 | 0.081774 | 2.210526 |
    | 16.01. |   2.075293 |             0.0 |         2.210526 |             2.075293 |                      1.075293 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |        0.000063 | 0.000063 |    2.075293 |    2.0 |   0.0 | 0.000063 | 2.368421 |
    | 17.01. |   2.249533 |             0.0 |         2.368421 |             2.249533 |                      1.249533 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.249533 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |   2.423773 |             0.0 |         2.526316 |             2.423773 |                      1.423773 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.423773 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |   2.598013 |             0.0 |         2.684211 |             2.598013 |                      1.598013 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.598013 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |   2.772253 |             0.0 |         2.842105 |             2.772253 |                      1.772253 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    2.772253 |    2.0 |   0.0 |      0.0 |      3.0 |

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
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | effectivewaterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxforceddischarge | maxfreedischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.174533 |             0.0 |              0.0 |             0.174533 |                           0.0 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.013278 |    2.0 |           0.0 |                0.0 |              0.0 |             0.0 |      0.0 |    0.174533 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |    0.34883 |             0.0 |              0.0 |              0.34883 |                      0.000001 |           2.0 |              0.033333 |                  1.0 |               0.016 |             0.016 |    2.0 |      0.000001 |                0.0 |         0.000001 |             0.0 | 0.000001 |     0.34883 |    2.0 |   0.0 | 0.000001 | 0.157895 |
    | 03.01. |   0.523081 |             0.0 |         0.157895 |             0.523082 |                      0.000019 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    2.0 |       0.00001 |                0.0 |          0.00001 |             0.0 |  0.00001 |    0.523081 |    2.0 |   0.0 |  0.00001 | 0.315789 |
    | 04.01. |   0.697313 |             0.0 |         0.315789 |             0.697307 |                      0.000352 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    2.0 |      0.000116 |                0.0 |         0.000116 |             0.0 | 0.000116 |    0.697313 |    2.0 |   0.0 | 0.000116 | 0.473684 |
    | 05.01. |   0.871372 |             0.0 |         0.473684 |              0.87137 |                      0.006359 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    2.0 |      0.002101 |                0.0 |         0.002101 |             0.0 | 0.002101 |    0.871372 |    2.0 |   0.0 | 0.002101 | 0.631579 |
    | 06.01. |   1.043195 |             0.0 |         0.631579 |             1.043194 |                      0.066439 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |      0.027981 |                0.0 |         0.027981 |             0.0 | 0.027981 |    1.043195 |    2.0 |   0.0 | 0.027981 | 0.789474 |
    | 07.01. |    1.20585 |             0.0 |         0.789474 |              1.20585 |                      0.207642 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |      0.134088 |                0.0 |         0.134088 |             0.0 | 0.134088 |     1.20585 |    2.0 |   0.0 | 0.134088 | 0.947368 |
    | 08.01. |   1.355683 |             0.0 |         0.947368 |             1.355688 |                      0.355832 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.282479 |                0.0 |         0.282479 |             0.0 | 0.282479 |    1.355683 |    2.0 |   0.0 | 0.282479 | 1.105263 |
    | 09.01. |   1.493163 |             0.0 |         1.105263 |             1.493167 |                      0.493181 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.425468 |                0.0 |         0.425468 |             0.0 | 0.425468 |    1.493163 |    2.0 |   0.0 | 0.425468 | 1.263158 |
    | 10.01. |   1.619267 |             0.0 |         1.263158 |             1.619271 |                      0.619272 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.557129 |                0.0 |         0.557129 |             0.0 | 0.557129 |    1.619267 |    2.0 |   0.0 | 0.557129 | 1.421053 |
    | 11.01. |   1.734934 |             0.0 |         1.421053 |             1.734937 |                      0.734937 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.677934 |                0.0 |         0.677934 |             0.0 | 0.677934 |    1.734934 |    2.0 |   0.0 | 0.677934 | 1.578947 |
    | 12.01. |   1.841026 |             0.0 |         1.578947 |             1.841029 |                      0.841029 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.788744 |                0.0 |         0.788744 |             0.0 | 0.788744 |    1.841026 |    2.0 |   0.0 | 0.788744 | 1.736842 |
    | 13.01. |   1.938337 |             0.0 |         1.736842 |              1.93834 |                       0.93834 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.890378 |                0.0 |         0.890383 |             0.0 | 0.890378 |    1.938337 |    2.0 |   0.0 | 0.890378 | 1.894737 |
    | 14.01. |   2.028235 |             0.0 |         1.894737 |             2.028237 |                      1.028237 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.976187 |                0.0 |         0.983929 |             0.0 | 0.976187 |    2.028235 |    2.0 |   0.0 | 0.976187 | 2.052632 |
    | 15.01. |   2.194622 |             0.0 |         2.052632 |             2.194622 |                      1.194622 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.090894 |                0.0 |         1.111526 |             0.0 | 0.090894 |    2.194622 |    2.0 |   0.0 | 0.090894 | 2.210526 |
    | 16.01. |   2.368855 |             0.0 |         2.210526 |             2.368855 |                      1.368855 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.000081 |                0.0 |         1.281738 |             0.0 | 0.000081 |    2.368855 |    2.0 |   0.0 | 0.000081 | 2.368421 |
    | 17.01. |   2.543095 |             0.0 |         2.368421 |             2.543095 |                      1.543095 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.455975 |             0.0 |      0.0 |    2.543095 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |   2.717335 |             0.0 |         2.526316 |             2.717335 |                      1.717335 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.630215 |             0.0 |      0.0 |    2.717335 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |   2.891575 |             0.0 |         2.684211 |             2.891575 |                      1.891575 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.804455 |             0.0 |      0.0 |    2.891575 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |   3.065815 |             0.0 |         2.842105 |             3.065815 |                      2.065815 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                0.0 |         1.978695 |             0.0 |      0.0 |    3.065815 |    2.0 |   0.0 |      0.0 |      3.0 |

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
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | effectivewaterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxforceddischarge | maxfreedischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.174533 |             0.0 |              0.0 |             0.174533 |                           0.0 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.013278 |    2.0 |           0.0 |                1.0 |              0.0 |             0.0 |      0.0 |    0.174533 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |    0.34883 |             0.0 |              0.0 |              0.34883 |                      0.000001 |           2.0 |              0.033333 |                  1.0 |               0.016 |             0.016 |    2.0 |      0.000001 |                1.0 |         0.000001 |             0.0 | 0.000001 |     0.34883 |    2.0 |   0.0 | 0.000001 | 0.157895 |
    | 03.01. |   0.523081 |             0.0 |         0.157895 |             0.523082 |                      0.000019 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    2.0 |       0.00001 |                1.0 |          0.00001 |             0.0 |  0.00001 |    0.523081 |    2.0 |   0.0 |  0.00001 | 0.315789 |
    | 04.01. |   0.697313 |             0.0 |         0.315789 |             0.697307 |                      0.000352 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    2.0 |      0.000116 |                1.0 |         0.000116 |             0.0 | 0.000116 |    0.697313 |    2.0 |   0.0 | 0.000116 | 0.473684 |
    | 05.01. |   0.871343 |             0.0 |         0.473684 |             0.871342 |                      0.006356 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    2.0 |        0.0021 |                1.0 |           0.0021 |        0.000339 | 0.002439 |    0.871343 |    2.0 |   0.0 | 0.002439 | 0.631579 |
    | 06.01. |   1.023411 |             0.0 |         0.631579 |             1.023419 |                      0.053844 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |      0.025696 |                1.0 |         0.025696 |        0.230921 | 0.256617 |    1.023411 |    2.0 |   0.0 | 0.256617 | 0.789474 |
    | 07.01. |   1.109653 |             0.0 |         0.789474 |             1.109654 |                      0.118252 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |      0.085557 |                1.0 |         0.085557 |        0.932947 | 1.018504 |    1.109653 |    2.0 |   0.0 | 1.018504 | 0.947368 |
    | 08.01. |   1.184465 |             0.0 |         0.947368 |              1.18447 |                      0.187025 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.152563 |                1.0 |         0.152563 |        0.998217 |  1.15078 |    1.184465 |    2.0 |   0.0 |  1.15078 | 1.105263 |
    | 09.01. |    1.25323 |             0.0 |         1.105263 |             1.253232 |                      0.254043 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.220842 |                1.0 |         0.220842 |        0.999938 |  1.22078 |     1.25323 |    2.0 |   0.0 |  1.22078 | 1.263158 |
    | 10.01. |   1.316381 |             0.0 |         1.263158 |             1.316383 |                      0.316663 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.285752 |                1.0 |         0.285752 |        0.999997 | 1.285749 |    1.316381 |    2.0 |   0.0 | 1.285749 | 1.421053 |
    | 11.01. |   1.374331 |             0.0 |         1.421053 |             1.374333 |                      0.374438 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |       0.34595 |                1.0 |          0.34595 |             1.0 | 1.345949 |    1.374331 |    2.0 |   0.0 | 1.345949 | 1.578947 |
    | 12.01. |   1.427493 |             0.0 |         1.578947 |             1.427495 |                      0.427538 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.401364 |                1.0 |         0.401364 |             1.0 | 1.401364 |    1.427493 |    2.0 |   0.0 | 1.401364 | 1.736842 |
    | 13.01. |   1.476259 |             0.0 |         1.736842 |              1.47626 |                      0.476279 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.452254 |                1.0 |         0.452256 |        0.999994 | 1.452248 |    1.476259 |    2.0 |   0.0 | 1.452248 | 1.894737 |
    | 14.01. |   1.521966 |             0.0 |         1.894737 |             1.521967 |                      0.521976 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.495522 |                1.0 |         0.499452 |        0.992131 | 1.487653 |    1.521966 |    2.0 |   0.0 | 1.487653 | 2.052632 |
    | 15.01. |   1.684877 |             0.0 |         2.052632 |             1.684877 |                      0.684877 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |       0.04935 |                1.0 |          0.60352 |        0.081774 | 0.131124 |    1.684877 |    2.0 |   0.0 | 0.131124 | 2.210526 |
    | 16.01. |   1.859107 |             0.0 |         2.210526 |             1.859107 |                      0.859107 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.000048 |                1.0 |         0.771992 |        0.000063 | 0.000111 |    1.859107 |    2.0 |   0.0 | 0.000111 | 2.368421 |
    | 17.01. |   2.033347 |             0.0 |         2.368421 |             2.033347 |                      1.033347 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         0.946227 |             0.0 |      0.0 |    2.033347 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |   2.207587 |             0.0 |         2.526316 |             2.207587 |                      1.207587 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         1.120467 |             0.0 |      0.0 |    2.207587 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |   2.381827 |             0.0 |         2.684211 |             2.381827 |                      1.381827 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         1.294707 |             0.0 |      0.0 |    2.381827 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |   2.556067 |             0.0 |         2.842105 |             2.556067 |                      1.556067 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |                1.0 |         1.468947 |             0.0 |      0.0 |    2.556067 |    2.0 |   0.0 |      0.0 |      3.0 |

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
import hydpy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.exe.modelimports import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(dam_model.Main_PrecipModel_V2, dam_model.Main_PEModel_V1):
    """Pumping station combined with a sluice."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        dam_model.Calc_Precipitation_V1,
        dam_model.Calc_PotentialEvaporation_V1,
        dam_model.Calc_AdjustedEvaporation_V1,
    )
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
    SUBMODELINTERFACES = (precipinterfaces.PrecipModel_V2, petinterfaces.PETModel_V1)
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)

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
