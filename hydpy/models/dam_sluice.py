# pylint: disable=line-too-long, unused-wildcard-import
"""|dam_sluice| is similar to |dam_pump| but is thought for modelling free flow through
sluices driven by differences between inner and outer water levels.  Principally, users
can define arbitrary relationships via |WaterLevelDifference2MaxFreeDischarge|,
including ones that allow for "negative outflow" so that |dam_sluice| takes water from
the downstream model.  However, be careful with that because, depending on the
downstream model's type and the current conditions, negative inflows can cause
problems.

By default, |dam_sluice| neither takes precipitation nor evaporation into account, but
you can add submodels that comply with the |PrecipModel_V2| or |PETModel_V1| interface
that supply this information.

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

>>> with model.add_precipmodel_v2("meteo_precip_io"):
...     precipitationfactor(1.0)
>>> with model.add_pemodel_v1("evap_ret_io"):
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
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | effectivewaterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxfreedischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.174533 |             0.0 |              0.0 |                           0.0 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.013278 |    2.0 |           0.0 |              0.0 |      0.0 |    0.174533 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |    0.34883 |             0.0 |              0.0 |                      0.000001 |           2.0 |              0.033333 |                  1.0 |               0.016 |             0.016 |    2.0 |      0.000001 |         0.000001 | 0.000001 |     0.34883 |    2.0 |   0.0 | 0.000001 | 0.157895 |
    | 03.01. |   0.523081 |             0.0 |         0.157895 |                      0.000019 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    2.0 |       0.00001 |          0.00001 |  0.00001 |    0.523081 |    2.0 |   0.0 |  0.00001 | 0.315789 |
    | 04.01. |   0.697313 |             0.0 |         0.315789 |                      0.000352 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    2.0 |      0.000116 |         0.000116 | 0.000116 |    0.697313 |    2.0 |   0.0 | 0.000116 | 0.473684 |
    | 05.01. |   0.871372 |             0.0 |         0.473684 |                      0.006359 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    2.0 |      0.002101 |         0.002101 | 0.002101 |    0.871372 |    2.0 |   0.0 | 0.002101 | 0.631579 |
    | 06.01. |   1.043195 |             0.0 |         0.631579 |                      0.066439 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |      0.027981 |         0.027981 | 0.027981 |    1.043195 |    2.0 |   0.0 | 0.027981 | 0.789474 |
    | 07.01. |    1.20585 |             0.0 |         0.789474 |                      0.207642 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |      0.134088 |         0.134088 | 0.134088 |     1.20585 |    2.0 |   0.0 | 0.134088 | 0.947368 |
    | 08.01. |   1.355683 |             0.0 |         0.947368 |                      0.355832 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.282479 |         0.282479 | 0.282479 |    1.355683 |    2.0 |   0.0 | 0.282479 | 1.105263 |
    | 09.01. |   1.493163 |             0.0 |         1.105263 |                      0.493181 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.425468 |         0.425468 | 0.425468 |    1.493163 |    2.0 |   0.0 | 0.425468 | 1.263158 |
    | 10.01. |   1.619267 |             0.0 |         1.263158 |                      0.619272 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.557129 |         0.557129 | 0.557129 |    1.619267 |    2.0 |   0.0 | 0.557129 | 1.421053 |
    | 11.01. |   1.734934 |             0.0 |         1.421053 |                      0.734937 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.677934 |         0.677934 | 0.677934 |    1.734934 |    2.0 |   0.0 | 0.677934 | 1.578947 |
    | 12.01. |   1.841026 |             0.0 |         1.578947 |                      0.841029 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.788744 |         0.788744 | 0.788744 |    1.841026 |    2.0 |   0.0 | 0.788744 | 1.736842 |
    | 13.01. |   1.938337 |             0.0 |         1.736842 |                       0.93834 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.890378 |         0.890383 | 0.890378 |    1.938337 |    2.0 |   0.0 | 0.890378 | 1.894737 |
    | 14.01. |   2.028235 |             0.0 |         1.894737 |                      1.028237 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.976187 |         0.983929 | 0.976187 |    2.028235 |    2.0 |   0.0 | 0.976187 | 2.052632 |
    | 15.01. |   2.194622 |             0.0 |         2.052632 |                      1.194622 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.090894 |         1.111526 | 0.090894 |    2.194622 |    2.0 |   0.0 | 0.090894 | 2.210526 |
    | 16.01. |   2.368855 |             0.0 |         2.210526 |                      1.368855 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.000081 |         1.281738 | 0.000081 |    2.368855 |    2.0 |   0.0 | 0.000081 | 2.368421 |
    | 17.01. |   2.543095 |             0.0 |         2.368421 |                      1.543095 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.455975 |      0.0 |    2.543095 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |   2.717335 |             0.0 |         2.526316 |                      1.717335 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.630215 |      0.0 |    2.717335 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |   2.891575 |             0.0 |         2.684211 |                      1.891575 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.804455 |      0.0 |    2.891575 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |   3.065815 |             0.0 |         2.842105 |                      2.065815 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |         1.978695 |      0.0 |    3.065815 |    2.0 |   0.0 |      0.0 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_sluice_irrigation:

irrigation
__________

The flow through the hydraulic structure can be negative, corresponding to irrigation
instead of land drainage.  We set the dam's "normal" inflow (from upstream areas) to
0 m³/s and increase the outer water level to 2 m, which reverses the water level
gradient:

>>> inflow.sequences.sim.series = 0.0
>>> outer.sequences.sim.series = 2.0

Now, the inner water level rises because of inflow from the area downstream.  The
remote water level still overshoots the threshold of 2 m, but this does not suppress
the inflow, as water losses should never increase flood risks:

.. integration-test::

    >>> test("dam_sluice_irrigation")
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | effectivewaterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxfreedischarge |   outflow | watervolume | inflow | outer |   outflow |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.001813 |             0.0 |              0.0 |                           0.0 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.012345 |    0.0 |           0.0 |              0.0 |       0.0 |    0.001813 |    0.0 |   2.0 |       0.0 |      0.0 |
    | 02.01. |   0.089711 |             2.0 |              0.0 |                          -1.0 |           2.0 |              0.033333 |                  1.0 |               0.016 |          0.015998 |    0.0 |          -1.0 |             -1.0 |      -1.0 |    0.089711 |    0.0 |   2.0 |      -1.0 | 0.157895 |
    | 03.01. |   0.177563 |             2.0 |         0.157895 |                          -1.0 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    0.0 |          -1.0 |             -1.0 |      -1.0 |    0.177563 |    0.0 |   2.0 |      -1.0 | 0.315789 |
    | 04.01. |   0.265405 |             2.0 |         0.315789 |                          -1.0 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    0.0 |          -1.0 |             -1.0 |      -1.0 |    0.265405 |    0.0 |   2.0 |      -1.0 | 0.473684 |
    | 05.01. |   0.353245 |             2.0 |         0.473684 |                     -0.999999 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    0.0 |     -0.999999 |        -0.999999 | -0.999999 |    0.353245 |    0.0 |   2.0 | -0.999999 | 0.631579 |
    | 06.01. |   0.441085 |             2.0 |         0.631579 |                     -0.999995 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    0.0 |     -0.999997 |        -0.999997 | -0.999997 |    0.441085 |    0.0 |   2.0 | -0.999997 | 0.789474 |
    | 07.01. |   0.528924 |             2.0 |         0.789474 |                      -0.99998 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    0.0 |     -0.999987 |        -0.999987 | -0.999987 |    0.528924 |    0.0 |   2.0 | -0.999987 | 0.947368 |
    | 08.01. |   0.616759 |             2.0 |         0.947368 |                      -0.99991 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.999945 |        -0.999945 | -0.999945 |    0.616759 |    0.0 |   2.0 | -0.999945 | 1.105263 |
    | 09.01. |   0.704581 |             2.0 |         1.105263 |                     -0.999602 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.999792 |        -0.999792 | -0.999792 |    0.704581 |    0.0 |   2.0 | -0.999792 | 1.263158 |
    | 10.01. |   0.792343 |             2.0 |         1.263158 |                     -0.998262 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.999089 |        -0.999089 | -0.999089 |    0.792343 |    0.0 |   2.0 | -0.999089 | 1.421053 |
    | 11.01. |   0.879846 |             2.0 |         1.421053 |                     -0.992719 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.996107 |        -0.996107 | -0.996107 |    0.879846 |    0.0 |   2.0 | -0.996107 | 1.578947 |
    | 12.01. |   0.966376 |             2.0 |         1.578947 |                      -0.97347 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.984837 |        -0.984837 | -0.984837 |    0.966376 |    0.0 |   2.0 | -0.984837 | 1.736842 |
    | 13.01. |   1.050185 |             2.0 |         1.736842 |                     -0.928748 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.953341 |        -0.953341 | -0.953341 |    1.050185 |    0.0 |   2.0 | -0.953341 | 1.894737 |
    | 14.01. |   1.129174 |             2.0 |         1.894737 |                     -0.864517 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.897562 |        -0.897562 | -0.897562 |    1.129174 |    0.0 |   2.0 | -0.897562 | 2.052632 |
    | 15.01. |   1.202334 |             2.0 |         2.052632 |                     -0.795763 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.830094 |        -0.830094 | -0.830094 |    1.202334 |    0.0 |   2.0 | -0.830094 | 2.210526 |
    | 16.01. |   1.269646 |             2.0 |         2.210526 |                     -0.729737 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.762403 |        -0.762403 | -0.762403 |    1.269646 |    0.0 |   2.0 | -0.762403 | 2.368421 |
    | 17.01. |   1.331448 |             2.0 |         2.368421 |                     -0.668333 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.698632 |        -0.698631 | -0.698632 |    1.331448 |    0.0 |   2.0 | -0.698632 | 2.526316 |
    | 18.01. |   1.388154 |             2.0 |         2.526316 |                     -0.611761 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.639654 |        -0.639653 | -0.639654 |    1.388154 |    0.0 |   2.0 | -0.639654 | 2.684211 |
    | 19.01. |   1.440173 |             2.0 |         2.684211 |                     -0.559791 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |      -0.58541 |        -0.585407 |  -0.58541 |    1.440173 |    0.0 |   2.0 |  -0.58541 | 2.842105 |
    | 20.01. |    1.48789 |             2.0 |         2.842105 |                     -0.512093 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    0.0 |     -0.535608 |        -0.535601 | -0.535608 |     1.48789 |    0.0 |   2.0 | -0.535608 |      3.0 |

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
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | effectivewaterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | freedischarge | maxfreedischarge |   outflow | watervolume | inflow | outer |   outflow |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.174533 |             0.0 |              0.0 |                           0.0 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.013278 |    2.0 |           0.0 |              0.0 |       0.0 |    0.174533 |    2.0 |   2.0 |       0.0 |      0.0 |
    | 02.01. |    0.43523 |             2.0 |              0.0 |                     -0.999996 |           2.0 |              0.033333 |                  1.0 |               0.016 |             0.016 |    2.0 |     -0.999998 |        -0.999998 | -0.999998 |     0.43523 |    2.0 |   2.0 | -0.999998 | 0.157895 |
    | 03.01. |   0.695875 |             2.0 |         0.157895 |                     -0.999656 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    2.0 |     -0.999917 |        -0.999917 | -0.999917 |    0.695875 |    2.0 |   2.0 | -0.999917 | 0.315789 |
    | 04.01. |   0.956025 |             2.0 |         0.315789 |                     -0.977007 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    2.0 |     -0.994311 |        -0.994311 | -0.994311 |    0.956025 |    2.0 |   2.0 | -0.994311 | 0.473684 |
    | 05.01. |   1.207742 |             2.0 |         0.473684 |                     -0.790519 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    2.0 |     -0.896712 |        -0.896712 | -0.896712 |    1.207742 |    2.0 |   2.0 | -0.896712 | 0.631579 |
    | 06.01. |    1.44021 |             2.0 |         0.631579 |                      -0.55975 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |     -0.673935 |        -0.673935 | -0.673935 |     1.44021 |    2.0 |   2.0 | -0.673935 | 0.789474 |
    | 07.01. |   1.653469 |             2.0 |         0.789474 |                     -0.346524 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |     -0.451615 |        -0.451615 | -0.451615 |    1.653469 |    2.0 |   2.0 | -0.451615 | 0.947368 |
    | 08.01. |   1.849078 |             2.0 |         0.947368 |                     -0.150917 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |     -0.247317 |        -0.247317 | -0.247317 |    1.849078 |    2.0 |   2.0 | -0.247317 | 1.105263 |
    | 09.01. |   2.028495 |             2.0 |         1.105263 |                        0.0285 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |     -0.059921 |        -0.059921 | -0.059921 |    2.028495 |    2.0 |   2.0 | -0.059921 | 1.263158 |
    | 10.01. |   2.193061 |             2.0 |         1.263158 |                      0.193066 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.111964 |         0.111964 |  0.111964 |    2.193061 |    2.0 |   2.0 |  0.111964 | 1.421053 |
    | 11.01. |   2.344006 |             2.0 |         1.421053 |                       0.34401 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.269621 |         0.269621 |  0.269621 |    2.344006 |    2.0 |   2.0 |  0.269621 | 1.578947 |
    | 12.01. |   2.482456 |             2.0 |         1.578947 |                       0.48246 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.414229 |         0.414229 |  0.414229 |    2.482456 |    2.0 |   2.0 |  0.414229 | 1.736842 |
    | 13.01. |   2.609447 |             2.0 |         1.736842 |                      0.609451 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.546864 |         0.546867 |  0.546864 |    2.609447 |    2.0 |   2.0 |  0.546864 | 1.894737 |
    | 14.01. |   2.726363 |             2.0 |         1.894737 |                      0.726366 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.663479 |         0.668741 |  0.663479 |    2.726363 |    2.0 |   2.0 |  0.663479 | 2.052632 |
    | 15.01. |   2.894875 |             2.0 |         2.052632 |                      0.894875 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.066296 |         0.810718 |  0.066296 |    2.894875 |    2.0 |   2.0 |  0.066296 | 2.210526 |
    | 16.01. |    3.06911 |             2.0 |         2.210526 |                       1.06911 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |      0.000062 |         0.981992 |  0.000062 |     3.06911 |    2.0 |   2.0 |  0.000062 | 2.368421 |
    | 17.01. |    3.24335 |             2.0 |         2.368421 |                       1.24335 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.15623 |       0.0 |     3.24335 |    2.0 |   2.0 |       0.0 | 2.526316 |
    | 18.01. |    3.41759 |             2.0 |         2.526316 |                       1.41759 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.33047 |       0.0 |     3.41759 |    2.0 |   2.0 |       0.0 | 2.684211 |
    | 19.01. |    3.59183 |             2.0 |         2.684211 |                       1.59183 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.50471 |       0.0 |     3.59183 |    2.0 |   2.0 |       0.0 | 2.842105 |
    | 20.01. |    3.76607 |             2.0 |         2.842105 |                       1.76607 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |           0.0 |          1.67895 |       0.0 |     3.76607 |    2.0 |   2.0 |       0.0 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
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


class Model(
    dam_model.ELSIEModel,
    dam_model.MixinSimpleWaterBalance,
    dam_model.Main_PrecipModel_V2,
    dam_model.Main_PEModel_V1,
):
    """|dam_sluice.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Dam-Sluice", description="sluice model")
    __HYDPY_ROOTMODEL__ = True

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
        dam_solver.MaxEval,
        dam_solver.MaxCFL,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        dam_model.Calc_Precipitation_V1,
        dam_model.Calc_PotentialEvaporation_V1,
        dam_model.Calc_AdjustedEvaporation_V1,
    )
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = (
        dam_model.Pick_LoggedOuterWaterLevel_V1,
        dam_model.Pick_LoggedRemoteWaterLevel_V1,
    )
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pick_Inflow_V1,
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
    SUBMODELINTERFACES = (precipinterfaces.PrecipModel_V2, petinterfaces.PETModel_V1)
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)


tester = Tester()
cythonizer = Cythonizer()
