# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""
.. _`issue 89`: https://github.com/hydpy-dev/hydpy/issues/89

|ga_garto| implements GARTO, a "Green-Ampt infiltration with Redistribution" model that
"incorporates features from the Talbot-Ogden infiltration and redistribution method",
developed by :cite:t:`ref-Lai2015`.  Thankfully, two of its authors, Fred L. Ogden and
Cary A. Talbot, provided their source code (written in C), which we used to ensure
|ga_garto| mostly works like this original implementation.  However, there are also
some differences, which interested users find discussed in `issue 89`_.  The most
notable difference is that |ga_garto| generally assumes a hydrostatic groundwater
table, while the complete GARTO method also simulates groundwater dynamics (in terms of
vertically moving groundwater fronts).

GARTO combines the oriinal  Green-Ampt infiltration model with redistribution
equations.  In the Green-Ampt model, a saturated wetting front moves downwards in a
piston-like form through a homogeneous soil with constant initial moisture and assumes
rainfall intensity always exceeds infiltration intensity.  The redistribution equations
apply for periods with little or no rainfall.  When redistribution begins, a previously
saturated wetting front still grows in length but reduces its relative water content.
With the next heavy rainfall event, a new saturated front develops, and both the old
and the new front advance downwards.

One improvement of GARTO over simpler GAR approaches is that the number of active
wetting fronts is (principally) not restricted.  Wetting fronts only disappear when
being merged with other fronts, which happens when a newer (wetter) front overshoots an
older (dryer) one or when a wetting front reaches the soil's depth (the groundwater
table).  Due to approximating natural soil moisture distributions with multiple wetting
fronts, GARTO can cope with complex rainfall patterns with (long) hiatus periods,
making it a suitable tool for long-term simulations.

Another functionality required for long-term simulations is evapotranspiration, which
is not discussed by :cite:t:`ref-Lai2015` but implemented in the mentioned C code.
|ga_garto| requires the complete withdrawal to be calculated externally and takes it
from the surface water and the wettest wetting fronts like one can do with the author's
GARTO code for evaporation.  The additional transpiration features of the C code (e.g.
taking rooted depth into account) are neglected since we expect |ga_garto| to be
applied for modelling the rooted soil zone.

ToDo: Taking the rooted depth as the depth of the considered soil domain and assuming a
      hydrostatic groundwater table at the soil's bottom do not go hand in hand for
      many catchments.  Do we need alternative lower boundary conditions?

.. _ga_garto_integration_tests:

Integration tests
=================

.. how_to_understand_integration_tests::

We prepare an initialisation period of 24 hours but restrict the actual simulation and
evaluation period to 5 hours for the first examples:

>>> from hydpy import pub
>>> pub.timegrids = "2000-01-01 00:00", "2000-01-02 00:00", "1h"
>>> pub.timegrids.sim.lastdate = pub.timegrids.eval_.lastdate = "2000-01-01 05:00"

We prepare a |ga_garto| model, set the base time for defining (most) time-dependent
parameter values to one hour, connect the model to an |Element| instance, and hand this
element to an |IntegrationTest| instance that will execute and evaluate the following
example simulations:

>>> from hydpy.models.ga_garto import *
>>> parameterstep("1h")
>>> from hydpy import Element, IntegrationTest
>>> soil = Element("soil")
>>> soil.model = model
>>> test = IntegrationTest(soil)
>>> test.dateformat = "%H:%M"
>>> test.plotting_options.axis1 = (inputs.rainfall, fluxes.infiltration,
...                                fluxes.surfacerunoff, fluxes.percolation,
...                                fluxes.withdrawal)
>>> test.plotting_options.axis2 = states.frontdepth

For the first set of examples, we initialise a single soil compartment (via parameter
|NmbSoils|) consisting of three "bins" (via parameter |NmbBins|).  So, besides the
first "filled" bin, there can be at most two active wetting fronts at the same time:

>>> nmbsoils(1)
>>> nmbbins(3)

We set the length of the numerical substeps to one second:

>>> with pub.options.parameterstep("1s"):
...     dt(1.0)

The single soil compartment is not sealed, meaning infiltration is possible:

>>> sealed(False)

The defined subarea is irrelevant as long as we deal with a single compartment:

>>> soilarea(2.0)

We perform all tests for an "average" soil (loam) and take its parameters from
:cite:t:`ref-Lai2015`, table 1:

>>> residualmoisture(0.027)
>>> saturationmoisture(0.434)
>>> saturatedconductivity(13.2)
>>> poresizedistribution(0.252)
>>> airentrypotential(111.5)

In agreement with the evaluations performed by :cite:t:`ref-Lai2015`, all our test runs
start with a relative moisture content of 10 %:

>>> test.inits = ((states.moisture, 0.1),
...               (states.frontdepth, 0.0),
...               (logs.moisturechange, 0.0))


5 hours, no evaporation, no capillary rise
__________________________________________

In this subsection, we focus on a short simulation period of five hours without any
evaporation losses or capillary rise gains.  The chosen rainfall pattern stems from
:cite:t:`ref-Lai2015`, table 2  (soil number 4, loam):

>>> inputs.rainfall.series[:5] = [40.0, 0.0, 0.0, 40.0, 0.0]
>>> inputs.evaporation.series = 0.0
>>> inputs.capillaryrise.series = 0.0

The next commands store the current initial conditions, so we can use them later to
check that |ga_garto| is not violating the water balance:

>>> test.reset_inits()
>>> conditions = sequences.conditions

.. _ga_garto_5h_1000mm:

deep soil
---------

In this example, we set the soil compartment's depth to one meter so that it does not
restrict the movement of any front:

>>> soildepth(1000.0)

The infiltration sums for the first and the second event agree well but not perfectly
with the results reported by :cite:t:`ref-Lai2015`, table 3  (soil number 4, loam),
which are 38.62 mm (instead of 38.90 mm) and  29.67 mm (instead of 30.01 mm).  We
checked if the different lengths of the numerical substeps (10 s vs 1 s) cause this
error, but they do not.  The authors' GARTO code, which we adapted to the same example,
also using a numerical substep length of 1 s, calculates the same infiltration sums as
|ga_garto| (38.90 mm and 30.01 mm).

The water content equals the saturation water content at the end of both rainfall
impulses and decreases afterwards.  Inspecting the front depths', it looks like
everything takes place in the second bin.  However, |ga_garto| actually creates a
second wetting front in the third bin during the second impulse, but this front reaches
the first one during the same simulation step, so they both get merged in the second
bin:

.. integration-test::

    >>> test("ga_garto_5h_1000mm")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                moisture |                     frontdepth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    38.896943 |         0.0 |               0.0 |        0.0 |      1.103057 |         38.896943 |              0.0 |                    0.0 |             0.0 |           1.103057 | 0.1     0.434       0.1 | 1000.0  116.457913         0.0 |
    | 01:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.364279       0.1 | 1000.0   147.18132         0.0 |
    | 02:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.343632       0.1 | 1000.0  159.654404         0.0 |
    | 03:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    30.008647 |         0.0 |               0.0 |        0.0 |      9.991353 |         30.008647 |              0.0 |                    0.0 |             0.0 |           9.991353 | 0.1     0.434       0.1 | 1000.0  206.304161         0.0 |
    | 04:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.387446       0.1 | 1000.0  239.716877         0.0 |

There is no indication of an error in the water balance:

>>> from hydpy import round_
>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_200mm:

200 mm depth
------------

Next, we repeat the above example with a reduced soil depth of 200 mm:

>>> soildepth(200.0)

All results for the first three hours are identical to those of the
:ref:`ga_garto_5h_1000mm` example.  But during the second rainfall event, the saturated
wetting front reaches the soil's bottom so that the first "filled" bin becomes
saturated and is the only active bin from then on.  Complete saturation comes with a
dramatic increase in actual conductivity through the whole soil column and thus in
percolation (groundwater recharge).  On the other hand, the overall downward water
movement and thus infiltration slows due to losing capillary drive after building
complete contact with groundwater:

.. integration-test::

    >>> test("ga_garto_5h_200mm")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                  moisture |                    frontdepth |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    38.896943 |         0.0 |               0.0 |        0.0 |      1.103057 |         38.896943 |              0.0 |                    0.0 |             0.0 |           1.103057 |   0.1     0.434       0.1 | 200.0  116.457913         0.0 |
    | 01:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 |   0.1  0.364279       0.1 | 200.0   147.18132         0.0 |
    | 02:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 |   0.1  0.343632       0.1 | 200.0  159.654404         0.0 |
    | 03:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |     29.03239 |    1.129333 |               0.0 |        0.0 |      10.96761 |          29.03239 |         1.129333 |                    0.0 |             0.0 |           10.96761 | 0.434     0.434     0.434 | 200.0         0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.434     0.434     0.434 | 200.0         0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_150mm:

150 mm depth
------------

When reducing the soil depth further to 150 mm, the first (and, so far, only) wetting
front reaches the soil's bottom yet in the first redistribution phase within the third
hour.  The soil water deficit at the start of the second rainfall event is smaller due
to increased relative moisture and the reduced soil depth, so infiltration declines
even more than in the :ref:`ga_garto_5h_200mm` example:

.. integration-test::

    >>> soildepth(150.0)
    >>> test("ga_garto_5h_150mm")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                    moisture |                    frontdepth |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    38.896943 |         0.0 |               0.0 |        0.0 |      1.103057 |         38.896943 |              0.0 |                    0.0 |             0.0 |           1.103057 |     0.1     0.434       0.1 | 150.0  116.457913         0.0 |
    | 01:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 |     0.1  0.364279       0.1 | 150.0   147.18132         0.0 |
    | 02:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |    0.000403 |               0.0 |        0.0 |           0.0 |               0.0 |         0.000403 |                    0.0 |             0.0 |                0.0 | 0.35931   0.35931   0.35931 | 150.0         0.0         0.0 |
    | 03:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    20.394407 |    9.190947 |               0.0 |        0.0 |     19.605593 |         20.394407 |         9.190947 |                    0.0 |             0.0 |          19.605593 |   0.434     0.434     0.434 | 150.0         0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 |   0.434     0.434     0.434 | 150.0         0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_100mm:

100 mm depth
------------

When reducing the soil depth even to 100 mm, the soil already saturates in the first
hour.  Then, the (potential) infiltration sum of the second event gets its smallest
possible value defined by saturated conductivity:

.. integration-test::

    >>> soildepth(100.0)
    >>> test("ga_garto_5h_100mm")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |               moisture |             frontdepth |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    35.497333 |    2.097333 |               0.0 |        0.0 |      4.502667 |         35.497333 |         2.097333 |                    0.0 |             0.0 |           4.502667 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 01:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 03:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |         13.2 |        13.2 |               0.0 |        0.0 |          26.8 |              13.2 |             13.2 |                    0.0 |             0.0 |               26.8 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

5 hours, evaporation
____________________

In this subsection, we repeat some of the above examples with an evaporation rate of
1 mm/h:

>>> inputs.evaporation.series = 1.0

.. _ga_garto_5h_1000mm_evap:

deep soil
---------

Repeating the :ref:`ga_garto_5h_1000mm` example but including evaporation reduces
surface runoff generation.  This effect emerges especially for the second event, where
evaporation has a cumulative impact due to also withdrawing water during the previous
redistribution phase:

.. integration-test::

    >>> soildepth(1000.0)
    >>> test("ga_garto_5h_1000mm_evap")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                moisture |                     frontdepth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    39.024721 |         0.0 |               0.0 |        1.0 |      0.727698 |         39.024721 |              0.0 |                    0.0 |             1.0 |           0.727698 | 0.1     0.434       0.1 | 1000.0   114.58773         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.358798       0.1 | 1000.0  144.020647         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.334277       0.1 | 1000.0  154.826468         0.0 |
    | 03:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    30.689523 |         0.0 |               0.0 |        1.0 |      8.547812 |         30.689523 |              0.0 |                    0.0 |             1.0 |           8.547812 | 0.1     0.434       0.1 | 1000.0  199.773922         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.383222       0.1 | 1000.0  232.060146         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_100mm_evap:

100 mm depth
------------

When repeating the :ref:`ga_garto_5h_100mm` example with evaporation, |ga_garto| does
not always withdraw water from the surface or the currently wettest wetting front (as
in the :ref:`ga_garto_5h_1000mm_evap` example) but (during rain-free periods) also from
the filled bin:

.. integration-test::

    >>> soildepth(100.0)
    >>> test("ga_garto_5h_100mm_evap")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                  moisture |             frontdepth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |     36.00042 |       1.848 |               0.0 |        1.0 |         3.752 |          36.00042 |            1.848 |                    0.0 |             1.0 |              3.752 | 0.434     0.434     0.434 | 100.0  0.0         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.424  0.424003  0.424003 | 100.0  0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.414  0.414003  0.414003 | 100.0  0.0         0.0 |
    | 03:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |      14.9125 |   12.848611 |               0.0 |        1.0 |     24.151389 |           14.9125 |        12.848611 |                    0.0 |             1.0 |          24.151389 | 0.434     0.434     0.434 | 100.0  0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.424  0.424003  0.424003 | 100.0  0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

4 mm depth
----------

Reducing the soil depth to 4 mm is surely no realistic configuration, but we use it to
show |ga_garto| works stably in case the soil runs completely dry during the third
hour:

.. integration-test::

    >>> soildepth(4.0)
    >>> test("ga_garto_5h_4mm_evap")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                  moisture |           frontdepth |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    14.450938 |   13.068271 |               0.0 |        1.0 |     24.595729 |         14.450938 |        13.068271 |                    0.0 |             1.0 |          24.595729 | 0.434     0.434     0.434 | 4.0  0.0         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.184  0.184069  0.184069 | 4.0  0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |      0.628 |           0.0 |               0.0 |              0.0 |                    0.0 |           0.628 |                0.0 | 0.027     0.027     0.027 | 4.0  0.0         0.0 |
    | 03:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    14.651938 |   12.969771 |               0.0 |        1.0 |     24.402229 |         14.651938 |        12.969771 |                    0.0 |             1.0 |          24.402229 | 0.434     0.434     0.434 | 4.0  0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.184  0.184069  0.184069 | 4.0  0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_1000mm_evap_10s:

deep soil, 10 sec
-----------------

In the following, we reuse the :ref:`ga_garto_5h_1000mm_evap` example to give an
impression of the relation between computational effort and numerical accuracy.  Please
consider this the first impression because such relationships can be distinctly
different for other conditions.  For example, setting the numerical substep length to
10 s (as done by :cite:t:`ref-Lai2015`) instead of 1 s (as in all our previous
examples) increases the total infiltration sum from 69.71 mm to 69.75 mm, which is an
irrelevant deviation for practical applications:

.. integration-test::

    >>> soildepth(1000.0)
    >>> with pub.options.parameterstep("1s"):
    ...     dt(10)
    >>> derived.nmbsubsteps.update()
    >>> test("ga_garto_5h_1000mm_evap_10sec")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                moisture |                     frontdepth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    39.035173 |         0.0 |               0.0 |        1.0 |      0.718436 |         39.035173 |              0.0 |                    0.0 |             1.0 |           0.718436 | 0.1     0.434       0.1 | 1000.0  114.615461         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.358667       0.1 | 1000.0   144.12976         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1    0.3342       0.1 | 1000.0  154.916779         0.0 |
    | 03:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    30.713686 |         0.0 |               0.0 |        1.0 |      8.524923 |         30.713686 |              0.0 |                    0.0 |             1.0 |           8.524923 | 0.1     0.434       0.1 | 1000.0  199.870182         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.383154       0.1 | 1000.0  232.229057         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_1000mm_evap_1min:

deep soil, 1 min
----------------

:cite:t:`ref-Lai2015` recommend using a numerical substep length of less than 1 min.
If we set it to 1 min exactly, the total infiltration sum increases from 69.7 mm to
69.9 mm.   Hence, at least for deep loam soils, calculating in 1 min intervals seems
acceptable for practical applications:

.. integration-test::

    >>> with pub.options.parameterstep("1m"):
    ...     dt(1)
    >>> derived.nmbsubsteps.update()
    >>> test("ga_garto_5h_1000mm_evap_1min")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                moisture |                     frontdepth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |     39.09203 |         0.0 |               0.0 |        1.0 |      0.667335 |          39.09203 |              0.0 |                    0.0 |             1.0 |           0.667335 | 0.1     0.434       0.1 | 1000.0  114.768457         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.357898       0.1 | 1000.0  144.757288         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.333753       0.1 | 1000.0   155.43215         0.0 |
    | 03:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    30.843714 |         0.0 |               0.0 |        1.0 |      8.405415 |         30.843714 |              0.0 |                    0.0 |             1.0 |           8.405415 | 0.1     0.434       0.1 | 1000.0  200.380986         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.382766       0.1 | 1000.0  233.151397         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_1000mm_evap_1hour:

deep soil, 1 hour
-----------------

This example shows that even when selecting way too long substeps (in this case, equal
to the simulation step size), |ga_garto| works stably and holds the water balance
(still, its results might be more or less random):

.. integration-test::

    >>> with pub.options.parameterstep("1h"):
    ...     dt(1.0)
    >>> derived.nmbsubsteps.update()
    >>> test("ga_garto_5h_1000mm_evap_1h")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                     moisture |                     frontdepth |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    35.149692 |         0.0 |               0.0 |        1.0 |      3.850308 |         35.149692 |              0.0 |                    0.0 |             1.0 |           3.850308 |      0.1     0.434       0.1 | 1000.0    105.2386         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 |  0.13415   0.13515   0.13515 | 1000.0         0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 |  0.13315   0.13415   0.13415 | 1000.0         0.0         0.0 |
    | 03:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    33.775558 |    0.000005 |               0.0 |        1.0 |      5.224442 |         33.775558 |         0.000005 |                    0.0 |             1.0 |           5.224442 |  0.13315     0.434   0.13415 | 1000.0  112.266969         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.165925  0.166925  0.166925 | 1000.0         0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

5 hours, capillary rise
_______________________

In this subsection, we repeat some of the above examples with a capillary rise rate of
1 mm/h:

>>> inputs.evaporation.series = 0.0
>>> inputs.capillaryrise.series = 1.0

We set the numerical substep length to 1 s, as in most examples above:

>>> with pub.options.parameterstep("1s"):
...     dt(1)
>>> derived.nmbsubsteps.update()

.. _ga_garto_5h_1000mm_caprise:

deep soil
---------

Repeating the :ref:`ga_garto_5h_1000mm` example but including capillary rise reduces
surface runoff generation.  This effect emerges especially for the second event, where
capillary rise has a cumulative impact due to also adding water during the previous
redistribution phase:

.. integration-test::

    >>> soildepth(1000.0)
    >>> test("ga_garto_5h_1000mm_caprise")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                     moisture |                     frontdepth |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           1.0 |         0.0 |               40.0 |             1.0 |    0.0 |     38.88927 |         0.0 |               1.0 |        0.0 |       1.11073 |          38.88927 |              0.0 |                    1.0 |             0.0 |            1.11073 | 0.101065     0.434  0.101065 | 1000.0  116.611777         0.0 |
    | 01:00 |      0.0 |           1.0 |         0.0 |                0.0 |             1.0 |    0.0 |          0.0 |         0.0 |               1.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    1.0 |             0.0 |                0.0 | 0.102222   0.36437  0.102222 | 1000.0  147.500306         0.0 |
    | 02:00 |      0.0 |           1.0 |         0.0 |                0.0 |             1.0 |    0.0 |          0.0 |         0.0 |               1.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    1.0 |             0.0 |                0.0 | 0.103405  0.343752  0.103405 | 1000.0  160.120235         0.0 |
    | 03:00 |     40.0 |           1.0 |         0.0 |               40.0 |             1.0 |    0.0 |    29.978803 |         0.0 |               1.0 |        0.0 |     10.021197 |         29.978803 |              0.0 |                    1.0 |             0.0 |          10.021197 | 0.104618     0.434  0.104618 | 1000.0  207.207357         0.0 |
    | 04:00 |      0.0 |           1.0 |         0.0 |                0.0 |             1.0 |    0.0 |          0.0 |         0.0 |               1.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    1.0 |             0.0 |                0.0 | 0.105912  0.387649  0.105912 | 1000.0  241.204907         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_100mm_caprise:

100 mm depth
------------

After decreasing the soil's depth to 100 mm, the soil can absorb the available
capillary rise only at the start of the simulation.  The actual soil water addition is
0.82 mm for the first hour instead of the potential 1.0 mm.  Afterwards, the soil is
full and cannot absorb any capillary rise:

.. integration-test::

    >>> soildepth(100.0)
    >>> test("ga_garto_5h_100mm_caprise")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |               moisture |             frontdepth |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           1.0 |         0.0 |               40.0 |             1.0 |    0.0 |    34.956278 |    2.376001 |          0.819722 |        0.0 |      5.043722 |         34.956278 |         2.376001 |               0.819722 |             0.0 |           5.043722 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 01:00 |      0.0 |           1.0 |         0.0 |                0.0 |             1.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 02:00 |      0.0 |           1.0 |         0.0 |                0.0 |             1.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 03:00 |     40.0 |           1.0 |         0.0 |               40.0 |             1.0 |    0.0 |         13.2 |        13.2 |               0.0 |        0.0 |          26.8 |              13.2 |             13.2 |                    0.0 |             0.0 |               26.8 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |
    | 04:00 |      0.0 |           1.0 |         0.0 |                0.0 |             1.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.434  0.434     0.434 | 100.0  0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_5h_1000mm_evap_caprise:

capillary rise and evaporation
------------------------------

In this example, we show what happens when simultaneously considering both capillary
rise and evaporation by assuming the same intensity of 1 mm/h:

>>> inputs.evaporation.series = 1.0

At first, one might assume |ga_garto| calculates the same infiltration rates as in the
:ref:`ga_garto_5h_1000mm` example because the capillary rise and evaporation cancel
each other out.  However, we see slightly higher infiltration rates as in the
:ref:`ga_garto_5h_1000mm` results due to the different "priorities" of both processes.
For evaporation, method |Withdraw_AllBins_V1| prefers to take water from the wettest
bin (proceeds from right to left).  For capillary rise, method |Withdraw_AllBins_V1|
prefers adding water to the dryest bin (proceeds from left to right):

.. integration-test::

    >>> soildepth(1000.0)
    >>> test("ga_garto_5h_1000mm_evap_caprise")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                     moisture |                     frontdepth |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           1.0 |         1.0 |               40.0 |             1.0 |    1.0 |    39.017221 |         0.0 |               1.0 |        1.0 |      0.734334 |         39.017221 |              0.0 |                    1.0 |             1.0 |           0.734334 | 0.101064     0.434  0.101064 | 1000.0  114.742841         0.0 |
    | 01:00 |      0.0 |           1.0 |         1.0 |                0.0 |             1.0 |    1.0 |          0.0 |         0.0 |               1.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    1.0 |             1.0 |                0.0 | 0.102218  0.358898  0.102218 | 1000.0  144.335188         0.0 |
    | 02:00 |      0.0 |           1.0 |         1.0 |                0.0 |             1.0 |    1.0 |          0.0 |         0.0 |               1.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    1.0 |             1.0 |                0.0 | 0.103395  0.334413  0.103395 | 1000.0  155.273537         0.0 |
    | 03:00 |     40.0 |           1.0 |         1.0 |               40.0 |             1.0 |    1.0 |     30.66013 |         0.0 |               1.0 |        1.0 |      8.576934 |          30.66013 |              0.0 |                    1.0 |             1.0 |           8.576934 | 0.104598     0.434  0.104598 | 1000.0  200.638186         0.0 |
    | 04:00 |      0.0 |           1.0 |         1.0 |                0.0 |             1.0 |    1.0 |          0.0 |         0.0 |               1.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    1.0 |             1.0 |                0.0 | 0.105881  0.383441  0.105881 | 1000.0  233.492414         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0


24 hours, no evaporation
________________________

In this and the following subsection, we deal with more complex series of rainfall
events spanning 24 hours: 

>>> pub.timegrids = pub.timegrids.init

The examples demonstrate how |ga_garto| works when pronounced hiatus periods occur,
where the accuracy of the redistribution process becomes highly important.
Additionally, we perform some "stress tests" to check the robustness of the interaction
of the different underlying methods.  We begin with a repeating pattern of hourly
rainfall sums of 0 mm and 40 mm and zero evaporation:

>>> inputs.rainfall.series = 12 * [0.0, 40.0]
>>> inputs.evaporation.series = 0.0
>>> inputs.capillaryrise.series = 0.0

The following "no evaporation" examples focus on a sufficiently deep soil column of 1 m
depth:

>>> soildepth(1000.0)

.. _ga_garto_24h_1000mm_3bins:

three bins
----------

For a series of 40 mm rainfall impulses, separated by hiatus periods of only one hour,
one should expect infiltration rates to decrease from event to event.  However, the
eleventh event (21:00 - 22:00) deviates from this expectation.  Inspecting the
evolution of the wetting fronts' relative moisture and depth reveals the cause.  For
the first event (01:00 - 02:00), a single saturated wetting front (handled by the
second bin) is sufficient.  For the next few subevents, an additional bin is required
for modelling new wetting fronts until they reach the old redistributing wetting front
of the second bin.  From the seventh event (13:00 - 14:00), the new wetting front
cannot reach the depth of the old wetting front during the event anymore, but still in
the subsequent hiatus period.  After the tenth event (19:00 - 20:00), the old front has
sufficiently grown to be out of reach for the new front, even during the hiatus period.
Then, |ga_garto| would need to activate a new bin to model the eleventh event with two
old and one new wetting front, which is impossible due to the limited number of
available bins:

ToDo: Should we think about increasing the number of bins automatically?

.. integration-test::

    >>> test("ga_garto_24h_1000mm_3bins")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                moisture |                     frontdepth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1       0.1       0.1 | 1000.0         0.0         0.0 |
    | 01:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    38.896943 |         0.0 |               0.0 |        0.0 |      1.103057 |         38.896943 |              0.0 |                    0.0 |             0.0 |           1.103057 | 0.1     0.434       0.1 | 1000.0  116.457913         0.0 |
    | 02:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.364279       0.1 | 1000.0   147.18132         0.0 |
    | 03:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    29.427627 |         0.0 |               0.0 |        0.0 |     10.572373 |         29.427627 |              0.0 |                    0.0 |             0.0 |          10.572373 | 0.1     0.434       0.1 | 1000.0  204.564581         0.0 |
    | 04:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.387148       0.1 | 1000.0  237.941999         0.0 |
    | 05:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    25.626714 |         0.0 |               0.0 |        0.0 |     14.373286 |         25.626714 |              0.0 |                    0.0 |             0.0 |          14.373286 | 0.1     0.434       0.1 | 1000.0  281.291271         0.0 |
    | 06:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.397405       0.1 | 1000.0  315.903728         0.0 |
    | 07:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    23.681158 |         0.0 |               0.0 |        0.0 |     16.318842 |         23.681158 |              0.0 |                    0.0 |             0.0 |          16.318842 | 0.1     0.434       0.1 | 1000.0  352.192943         0.0 |
    | 08:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.403518       0.1 | 1000.0  387.563853         0.0 |
    | 09:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    22.433986 |         0.0 |               0.0 |        0.0 |     17.566014 |         22.433986 |              0.0 |                    0.0 |             0.0 |          17.566014 | 0.1     0.434       0.1 | 1000.0  419.360565         0.0 |
    | 10:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.407664       0.1 | 1000.0  455.257579         0.0 |
    | 11:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    21.542888 |         0.0 |               0.0 |        0.0 |     18.457112 |         21.542888 |              0.0 |                    0.0 |             0.0 |          18.457112 | 0.1     0.434       0.1 | 1000.0   483.86023         0.0 |
    | 12:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.410698       0.1 | 1000.0  520.148824         0.0 |
    | 13:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    20.851521 |         0.0 |               0.0 |        0.0 |     19.148479 |         20.851521 |              0.0 |                    0.0 |             0.0 |          19.148479 | 0.1  0.410698     0.434 | 1000.0  549.592648  502.252611 |
    | 14:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.413271       0.1 | 1000.0  582.437628         0.0 |
    | 15:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    20.248024 |         0.0 |               0.0 |        0.0 |     19.751976 |         20.248024 |              0.0 |                    0.0 |             0.0 |          19.751976 | 0.1  0.413271     0.434 | 1000.0  613.068675  513.880136 |
    | 16:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.415161       0.1 | 1000.0  643.192319         0.0 |
    | 17:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |     19.76204 |         0.0 |               0.0 |        0.0 |      20.23796 |          19.76204 |              0.0 |                    0.0 |             0.0 |           20.23796 | 0.1  0.415161     0.434 | 1000.0  674.655072  522.639168 |
    | 18:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.416592       0.1 | 1000.0  702.704838         0.0 |
    | 19:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    19.363437 |         0.0 |               0.0 |        0.0 |     20.636563 |         19.363437 |              0.0 |                    0.0 |             0.0 |          20.636563 | 0.1  0.416592     0.434 | 1000.0  734.757786  529.403244 |
    | 20:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.416592   0.41723 | 1000.0  762.475214  690.509816 |
    | 21:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    20.503402 |         0.0 |               0.0 |        0.0 |     19.496598 |         20.503402 |              0.0 |                    0.0 |             0.0 |          19.496598 | 0.1  0.416592     0.434 | 1000.0  792.704507  653.366365 |
    | 22:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.418979       0.1 | 1000.0  822.429032         0.0 |
    | 23:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    18.677018 |         0.0 |               0.0 |        0.0 |     21.322982 |         18.677018 |              0.0 |                    0.0 |             0.0 |          21.322982 | 0.1  0.418979     0.434 | 1000.0  855.509696  540.914341 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_24h_1000mm_4bins:

four bins
---------

After setting the number of available bins to four, |ga_garto| can create all wetting
fronts required during the simulation period and predicts the infiltration rate
decrease expected for all events:

.. integration-test::

    >>> nmbbins(4)
    >>> test("ga_garto_24h_1000mm_4bins")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                         moisture |                                 frontdepth |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1       0.1      0.1       0.1 | 1000.0         0.0         0.0         0.0 |
    | 01:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    38.896943 |         0.0 |               0.0 |        0.0 |      1.103057 |         38.896943 |              0.0 |                    0.0 |             0.0 |           1.103057 | 0.1     0.434      0.1       0.1 | 1000.0  116.457913         0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.364279      0.1       0.1 | 1000.0   147.18132         0.0         0.0 |
    | 03:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    29.427627 |         0.0 |               0.0 |        0.0 |     10.572373 |         29.427627 |              0.0 |                    0.0 |             0.0 |          10.572373 | 0.1     0.434      0.1       0.1 | 1000.0  204.564581         0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.387148      0.1       0.1 | 1000.0  237.941999         0.0         0.0 |
    | 05:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    25.626714 |         0.0 |               0.0 |        0.0 |     14.373286 |         25.626714 |              0.0 |                    0.0 |             0.0 |          14.373286 | 0.1     0.434      0.1       0.1 | 1000.0  281.291271         0.0         0.0 |
    | 06:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.397405      0.1       0.1 | 1000.0  315.903728         0.0         0.0 |
    | 07:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    23.681158 |         0.0 |               0.0 |        0.0 |     16.318842 |         23.681158 |              0.0 |                    0.0 |             0.0 |          16.318842 | 0.1     0.434      0.1       0.1 | 1000.0  352.192943         0.0         0.0 |
    | 08:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.403518      0.1       0.1 | 1000.0  387.563853         0.0         0.0 |
    | 09:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    22.434993 |         0.0 |               0.0 |        0.0 |     17.565007 |         22.434993 |              0.0 |                    0.0 |             0.0 |          17.565007 | 0.1     0.434      0.1       0.1 | 1000.0   419.36358         0.0         0.0 |
    | 10:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.407664      0.1       0.1 | 1000.0  455.260614         0.0         0.0 |
    | 11:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    21.543879 |         0.0 |               0.0 |        0.0 |     18.456121 |         21.543879 |              0.0 |                    0.0 |             0.0 |          18.456121 | 0.1     0.434      0.1       0.1 | 1000.0  483.866211         0.0         0.0 |
    | 12:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.410698      0.1       0.1 | 1000.0  520.154838         0.0         0.0 |
    | 13:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    20.852762 |         0.0 |               0.0 |        0.0 |     19.147238 |         20.852762 |              0.0 |                    0.0 |             0.0 |          19.147238 | 0.1  0.410698    0.434       0.1 | 1000.0  549.604576  502.232076         0.0 |
    | 14:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.413271      0.1       0.1 | 1000.0  582.447698         0.0         0.0 |
    | 15:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    20.249245 |         0.0 |               0.0 |        0.0 |     19.750755 |         20.249245 |              0.0 |                    0.0 |             0.0 |          19.750755 | 0.1  0.413271    0.434       0.1 | 1000.0  613.084239  513.859417         0.0 |
    | 16:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.415161      0.1       0.1 | 1000.0  643.205436         0.0         0.0 |
    | 17:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    19.763163 |         0.0 |               0.0 |        0.0 |     20.236837 |         19.763163 |              0.0 |                    0.0 |             0.0 |          20.236837 | 0.1  0.415161    0.434       0.1 | 1000.0   674.67364  522.620811         0.0 |
    | 18:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.416593      0.1       0.1 | 1000.0   702.72179         0.0         0.0 |
    | 19:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    19.364813 |         0.0 |               0.0 |        0.0 |     20.635187 |         19.364813 |              0.0 |                    0.0 |             0.0 |          20.635187 | 0.1  0.416593    0.434       0.1 | 1000.0  734.780849  529.379914         0.0 |
    | 20:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.416593  0.41723       0.1 | 1000.0  762.498422   690.44692         0.0 |
    | 21:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |     19.10987 |         0.0 |               0.0 |        0.0 |      20.89013 |          19.10987 |              0.0 |                    0.0 |             0.0 |           20.89013 | 0.1   0.41723    0.434       0.1 | 1000.0  794.446748  532.431799         0.0 |
    | 22:00 |      0.0 |           0.0 |         0.0 |                0.0 |             0.0 |    0.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1   0.41723  0.41729       0.1 | 1000.0  822.468829  652.505949         0.0 |
    | 23:00 |     40.0 |           0.0 |         0.0 |               40.0 |             0.0 |    0.0 |    18.967684 |         0.0 |               0.0 |        0.0 |     21.032316 |         18.967684 |              0.0 |                    0.0 |             0.0 |          21.032316 | 0.1   0.41729    0.434       0.1 | 1000.0  854.161255   532.72863         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

24 hours, evaporation
_____________________

This subsection combines complex precipitation events with an evaporation rate of
1 mm/h:

>>> inputs.evaporation.series = 1.0

.. _ga_garto_24h_1000mm_evap:

multiple events
---------------

In contrast to the :ref:`ga_garto_5h_1000mm_evap` example, rainfall starts in the
second simulation step.  Hence, the initial moisture (handled by the first bin)
decreases during the first simulation step:

.. integration-test::

    >>> test("ga_garto_24h_1000mm_evap")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                            moisture |                                 frontdepth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099     0.099     0.099     0.099 | 1000.0         0.0         0.0         0.0 |
    | 01:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    39.041594 |         0.0 |               0.0 |        1.0 |      0.713078 |         39.041594 |              0.0 |                    0.0 |             1.0 |           0.713078 | 0.099     0.434     0.099     0.099 | 1000.0  114.289319         0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.358644     0.099     0.099 | 1000.0  143.607705         0.0         0.0 |
    | 03:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    29.920271 |         0.0 |               0.0 |        1.0 |      9.273387 |         29.920271 |              0.0 |                    0.0 |             1.0 |           9.273387 | 0.099     0.434     0.099     0.099 | 1000.0  200.040404         0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.383262     0.099     0.099 | 1000.0  232.228153         0.0         0.0 |
    | 05:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    26.151093 |         0.0 |               0.0 |        1.0 |     12.997939 |         26.151093 |              0.0 |                    0.0 |             1.0 |          12.997939 | 0.099     0.434     0.099     0.099 | 1000.0  274.673421         0.0         0.0 |
    | 06:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.394281     0.099     0.099 | 1000.0   308.23364         0.0         0.0 |
    | 07:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    24.246288 |         0.0 |               0.0 |        1.0 |     14.881992 |         24.246288 |              0.0 |                    0.0 |             1.0 |          14.881992 | 0.099     0.434     0.099     0.099 | 1000.0  343.682399         0.0         0.0 |
    | 08:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099   0.40086     0.099     0.099 | 1000.0  378.101578         0.0         0.0 |
    | 09:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    23.029243 |         0.0 |               0.0 |        1.0 |     16.085756 |         23.029243 |              0.0 |                    0.0 |             1.0 |          16.085756 | 0.099     0.434     0.099     0.099 | 1000.0  409.098052         0.0         0.0 |
    | 10:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099   0.40533     0.099     0.099 | 1000.0  444.121263         0.0         0.0 |
    | 11:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    22.159184 |         0.0 |               0.0 |        1.0 |     16.946127 |         22.159184 |              0.0 |                    0.0 |             1.0 |          16.946127 | 0.099     0.434     0.099     0.099 | 1000.0  471.945433         0.0         0.0 |
    | 12:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.408607     0.099     0.099 | 1000.0  507.422909         0.0         0.0 |
    | 13:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    21.486061 |         0.0 |               0.0 |        1.0 |      17.61165 |         21.486061 |              0.0 |                    0.0 |             1.0 |           17.61165 | 0.099  0.408607     0.434     0.099 | 1000.0  535.098528  504.856362         0.0 |
    | 14:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099    0.4113     0.099     0.099 | 1000.0  568.331329         0.0         0.0 |
    | 15:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |     20.90663 |         0.0 |               0.0 |        1.0 |     18.184482 |          20.90663 |              0.0 |                    0.0 |             1.0 |          18.184482 | 0.099    0.4113     0.434     0.099 | 1000.0  597.246501  519.184071         0.0 |
    | 16:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.413387     0.099     0.099 | 1000.0  627.587693         0.0         0.0 |
    | 17:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    20.421532 |         0.0 |               0.0 |        1.0 |      18.66414 |         20.421532 |              0.0 |                    0.0 |             1.0 |           18.66414 | 0.099  0.413387     0.434     0.099 | 1000.0  657.465384  530.870913         0.0 |
    | 18:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.414936     0.099     0.099 | 1000.0  685.713192         0.0         0.0 |
    | 19:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    20.025604 |         0.0 |               0.0 |        1.0 |     19.055781 |         20.025604 |              0.0 |                    0.0 |             1.0 |          19.055781 | 0.099  0.414936     0.434     0.099 | 1000.0  716.263636   539.87659         0.0 |
    | 20:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.414936  0.416189     0.099 | 1000.0  742.803107  724.318214         0.0 |
    | 21:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    19.689022 |         0.0 |               0.0 |        1.0 |     19.388809 |         19.689022 |              0.0 |                    0.0 |             1.0 |          19.388809 | 0.099  0.416189     0.434     0.099 | 1000.0  773.818616    547.4229         0.0 |
    | 22:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.099  0.416189  0.416346     0.099 | 1000.0  801.068162  680.245328         0.0 |
    | 23:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    19.538331 |         0.0 |               0.0 |        1.0 |     19.538741 |         19.538331 |              0.0 |                    0.0 |             1.0 |          19.538741 | 0.099  0.416346     0.434     0.099 | 1000.0  831.823337  548.446593         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_24h_1000mm_evap_continuous:

continuous event
----------------

Now, we define an extreme rainfall event with multiple increases and decreases in
intensity:

>>> inputs.rainfall.series = [
...     0.0, 10.0, 20.0, 10.0, 20.0, 30.0, 20.0, 30.0, 40.0, 30.0, 40.0, 50.0,
...     50.0, 40.0, 30.0, 40.0, 30.0, 20.0, 30.0, 20.0, 10.0, 20.0, 10.0, 0.0]

Because of the vast rainfall, the soil saturates entirely in the 20th hour, and
percolation becomes significant afterwards.  In the 21st hour, it is restricted by
saturated conductivity and in the 22nd hour, by the current rainfall rate.  Note there
is a difference in the behaviour especially relevant during the 21st hour, which we
discuss in the documentation on method |Redistribute_Front_V1|:

.. integration-test::

    >>> test("ga_garto_24h_1000mm_evap_continuous")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                               moisture |                          frontdepth |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 |    0.099     0.099     0.099     0.099 | 1000.0         0.0  0.0         0.0 |
    | 01:00 |     10.0 |           0.0 |         1.0 |               10.0 |             0.0 |    1.0 |         10.0 |         0.0 |               0.0 |        1.0 |           0.0 |              10.0 |              0.0 |                    0.0 |             1.0 |                0.0 |    0.099  0.362114     0.099     0.099 | 1000.0   34.205692  0.0         0.0 |
    | 02:00 |     20.0 |           0.0 |         1.0 |               20.0 |             0.0 |    1.0 |         20.0 |         0.0 |               0.0 |        1.0 |           0.0 |              20.0 |              0.0 |                    0.0 |             1.0 |                0.0 |    0.099  0.423016     0.099     0.099 | 1000.0   86.415369  0.0         0.0 |
    | 03:00 |     10.0 |           0.0 |         1.0 |               10.0 |             0.0 |    1.0 |         10.0 |         0.0 |               0.0 |        1.0 |           0.0 |              10.0 |              0.0 |                    0.0 |             1.0 |                0.0 |    0.099  0.401285     0.099     0.099 | 1000.0  122.401136  0.0         0.0 |
    | 04:00 |     20.0 |           0.0 |         1.0 |               20.0 |             0.0 |    1.0 |         20.0 |         0.0 |               0.0 |        1.0 |           0.0 |              20.0 |              0.0 |                    0.0 |             1.0 |                0.0 |    0.099  0.432646     0.099     0.099 | 1000.0  167.842713  0.0         0.0 |
    | 05:00 |     30.0 |           0.0 |         1.0 |               30.0 |             0.0 |    1.0 |    24.597228 |         0.0 |               0.0 |        1.0 |      4.402772 |         24.597228 |              0.0 |                    0.0 |             1.0 |           4.402772 |    0.099     0.434     0.099     0.099 | 1000.0  240.588739  0.0         0.0 |
    | 06:00 |     20.0 |           0.0 |         1.0 |               20.0 |             0.0 |    1.0 |         20.0 |         0.0 |               0.0 |        1.0 |           0.0 |              20.0 |              0.0 |                    0.0 |             1.0 |                0.0 |    0.099  0.433999     0.099     0.099 | 1000.0  297.305986  0.0         0.0 |
    | 07:00 |     30.0 |           0.0 |         1.0 |               30.0 |             0.0 |    1.0 |    20.265771 |         0.0 |               0.0 |        1.0 |      8.734229 |         20.265771 |              0.0 |                    0.0 |             1.0 |           8.734229 |    0.099     0.434     0.099     0.099 | 1000.0  357.799995  0.0         0.0 |
    | 08:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    19.185635 |         0.0 |               0.0 |        1.0 |     19.814365 |         19.185635 |              0.0 |                    0.0 |             1.0 |          19.814365 |    0.099     0.434     0.099     0.099 | 1000.0  415.070547  0.0         0.0 |
    | 09:00 |     30.0 |           0.0 |         1.0 |               30.0 |             0.0 |    1.0 |    18.424562 |         0.0 |               0.0 |        1.0 |     10.575438 |         18.424562 |              0.0 |                    0.0 |             1.0 |          10.575438 |    0.099     0.434     0.099     0.099 | 1000.0  470.069238  0.0         0.0 |
    | 10:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    17.854101 |         0.0 |               0.0 |        1.0 |     21.145899 |         17.854101 |              0.0 |                    0.0 |             1.0 |          21.145899 |    0.099     0.434     0.099     0.099 | 1000.0  523.365062  0.0         0.0 |
    | 11:00 |     50.0 |           0.0 |         1.0 |               50.0 |             0.0 |    1.0 |    17.407673 |         0.0 |               0.0 |        1.0 |     31.592327 |         17.407673 |              0.0 |                    0.0 |             1.0 |          31.592327 |    0.099     0.434     0.099     0.099 | 1000.0  575.328266  0.0         0.0 |
    | 12:00 |     50.0 |           0.0 |         1.0 |               50.0 |             0.0 |    1.0 |    17.047104 |         0.0 |               0.0 |        1.0 |     31.952896 |         17.047104 |              0.0 |                    0.0 |             1.0 |          31.952896 |    0.099     0.434     0.099     0.099 | 1000.0  626.215142  0.0         0.0 |
    | 13:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    16.748785 |         0.0 |               0.0 |        1.0 |     22.251215 |         16.748785 |              0.0 |                    0.0 |             1.0 |          22.251215 |    0.099     0.434     0.099     0.099 | 1000.0  676.211516  0.0         0.0 |
    | 14:00 |     30.0 |           0.0 |         1.0 |               30.0 |             0.0 |    1.0 |    16.497275 |         0.0 |               0.0 |        1.0 |     12.502725 |         16.497275 |              0.0 |                    0.0 |             1.0 |          12.502725 |    0.099     0.434     0.099     0.099 | 1000.0  725.457114  0.0         0.0 |
    | 15:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    16.282023 |         0.0 |               0.0 |        1.0 |     22.717977 |         16.282023 |              0.0 |                    0.0 |             1.0 |          22.717977 |    0.099     0.434     0.099     0.099 | 1000.0  774.060169  0.0         0.0 |
    | 16:00 |     30.0 |           0.0 |         1.0 |               30.0 |             0.0 |    1.0 |    16.095253 |         0.0 |               0.0 |        1.0 |     12.904747 |         16.095253 |              0.0 |                    0.0 |             1.0 |          12.904747 |    0.099     0.434     0.099     0.099 | 1000.0  822.105699  0.0         0.0 |
    | 17:00 |     20.0 |           0.0 |         1.0 |               20.0 |             0.0 |    1.0 |    15.931516 |         0.0 |               0.0 |        1.0 |      3.068484 |         15.931516 |              0.0 |                    0.0 |             1.0 |           3.068484 |    0.099     0.434     0.099     0.099 | 1000.0  869.662463  0.0         0.0 |
    | 18:00 |     30.0 |           0.0 |         1.0 |               30.0 |             0.0 |    1.0 |    15.786723 |         0.0 |               0.0 |        1.0 |     13.213277 |         15.786723 |              0.0 |                    0.0 |             1.0 |          13.213277 |    0.099     0.434     0.099     0.099 | 1000.0   916.78701  0.0         0.0 |
    | 19:00 |     20.0 |           0.0 |         1.0 |               20.0 |             0.0 |    1.0 |    15.657507 |         0.0 |               0.0 |        1.0 |      3.342493 |         15.657507 |              0.0 |                    0.0 |             1.0 |           3.342493 |    0.099     0.434     0.099     0.099 | 1000.0  963.525835  0.0         0.0 |
    | 20:00 |     10.0 |           0.0 |         1.0 |               10.0 |             0.0 |    1.0 |         10.0 |    0.867385 |               0.0 |        1.0 |           0.0 |              10.0 |         0.867385 |                    0.0 |             1.0 |                0.0 | 0.429914  0.429914  0.429914  0.429914 | 1000.0         0.0  0.0         0.0 |
    | 21:00 |     20.0 |           0.0 |         1.0 |               20.0 |             0.0 |    1.0 |    17.495333 |   12.776553 |               0.0 |        1.0 |      2.136333 |         17.495333 |        12.776553 |                    0.0 |             1.0 |           2.136333 | 0.434001  0.434001  0.434001  0.434001 | 1000.0         0.0  0.0         0.0 |
    | 22:00 |     10.0 |           0.0 |         1.0 |               10.0 |             0.0 |    1.0 |         10.0 |        10.0 |               0.0 |        1.0 |           0.0 |              10.0 |             10.0 |                    0.0 |             1.0 |                0.0 | 0.433001  0.433001  0.433001  0.433001 | 1000.0         0.0  0.0         0.0 |
    | 23:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.432001  0.432001  0.432001  0.432001 | 1000.0         0.0  0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_24h_1000mm_evap_interruptions:

long interruption
-----------------

We define three strong rainfall impulses with hiatus periods of ten and eleven hours to
give better insight into the longer-term behaviour of wetting front redistribution:

>>> inputs.rainfall.series = 0.0
>>> inputs.rainfall.series[[0, 11, 23]] = 40.0, 15.0, 15.0

The second, smaller rainfall impulse cause the creation of a second wetting front.
This front does not become fully saturated and requires about three hours for to reach
the first front's depth:

.. integration-test::

    >>> test("ga_garto_24h_1000mm_evap_interruptions")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                          moisture |                                 frontdepth |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |    39.024721 |         0.0 |               0.0 |        1.0 |      0.727698 |         39.024721 |              0.0 |                    0.0 |             1.0 |           0.727698 | 0.1     0.434       0.1       0.1 | 1000.0   114.58773         0.0         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.358798       0.1       0.1 | 1000.0  144.020647         0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.334277       0.1       0.1 | 1000.0  154.826468         0.0         0.0 |
    | 03:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.318405       0.1       0.1 | 1000.0  161.499839         0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.306195       0.1       0.1 | 1000.0  166.212888         0.0         0.0 |
    | 05:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.295993       0.1       0.1 | 1000.0  169.763106         0.0         0.0 |
    | 06:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.287043       0.1       0.1 | 1000.0  172.539757         0.0         0.0 |
    | 07:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1   0.27894       0.1       0.1 | 1000.0  174.764504         0.0         0.0 |
    | 08:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1   0.27144       0.1       0.1 | 1000.0  176.576626         0.0         0.0 |
    | 09:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.264387       0.1       0.1 | 1000.0  178.069861         0.0         0.0 |
    | 10:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.257672       0.1       0.1 | 1000.0  179.310578         0.0         0.0 |
    | 11:00 |     15.0 |           0.0 |         1.0 |               15.0 |             0.0 |    1.0 |         15.0 |         0.0 |               0.0 |        1.0 |           0.0 |              15.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.257672  0.408371       0.1 | 1000.0  179.504341   92.697947         0.0 |
    | 12:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.257672  0.348534       0.1 | 1000.0  179.691196     142.414         0.0 |
    | 13:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.257672  0.329314       0.1 | 1000.0  179.868591  166.271421         0.0 |
    | 14:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.316885       0.1       0.1 | 1000.0  181.074289         0.0         0.0 |
    | 15:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.306472       0.1       0.1 | 1000.0    185.3631         0.0         0.0 |
    | 16:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.297508       0.1       0.1 | 1000.0  188.713192         0.0         0.0 |
    | 17:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.289506       0.1       0.1 | 1000.0  191.404458         0.0         0.0 |
    | 18:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.282184       0.1       0.1 | 1000.0  193.608049         0.0         0.0 |
    | 19:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.275362       0.1       0.1 | 1000.0  195.436907         0.0         0.0 |
    | 20:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.268921       0.1       0.1 | 1000.0  196.969814         0.0         0.0 |
    | 21:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.262774       0.1       0.1 | 1000.0  198.264096         0.0         0.0 |
    | 22:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.256861       0.1       0.1 | 1000.0  199.362866         0.0         0.0 |
    | 23:00 |     15.0 |           0.0 |         1.0 |               15.0 |             0.0 |    1.0 |         15.0 |         0.0 |               0.0 |        1.0 |           0.0 |              15.0 |              0.0 |                    0.0 |             1.0 |                0.0 | 0.1  0.256861  0.408284       0.1 | 1000.0  199.547726   92.265084         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _ga_garto_24h_sealed:

sealed surface
--------------

One can mark individual soil compartments as "sealed":

>>> sealed(True)

Then, the soil's surface prevents infiltration and all rainfall evaporates, or becomes
surface runoff:

.. integration-test::

    >>> test("ga_garto_24h_sealed")
    |  date | rainfall | capillaryrise | evaporation | surfacewatersupply | soilwatersupply | demand | infiltration | percolation | soilwateraddition | withdrawal | surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                moisture |                frontdepth |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 |               40.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |          39.0 |               0.0 |              0.0 |                    0.0 |             1.0 |               39.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 03:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 05:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 06:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 07:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 08:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 09:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 10:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 11:00 |     15.0 |           0.0 |         1.0 |               15.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |          14.0 |               0.0 |              0.0 |                    0.0 |             1.0 |               14.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 12:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 13:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 14:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 15:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 16:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 17:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 18:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 19:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 20:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 21:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 22:00 |      0.0 |           0.0 |         1.0 |                0.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        0.0 |           0.0 |               0.0 |              0.0 |                    0.0 |             0.0 |                0.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |
    | 23:00 |     15.0 |           0.0 |         1.0 |               15.0 |             0.0 |    1.0 |          0.0 |         0.0 |               0.0 |        1.0 |          14.0 |               0.0 |              0.0 |                    0.0 |             1.0 |               14.0 | 0.1  0.1  0.1       0.1 | 0.0  0.0  0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0


.. _ga_garto_5h_3soils:

three compartments
------------------

We prepare three soil compartments within the same model instance, of which the last
one is sealed:

>>> nmbsoils(3)
>>> sealed(False, False, True)


We must define each compartment's area but only the depth of unsealed ones:

>>> soilarea(1.0, 2.0, 3.0)
>>> soildepth(400.0, 100.0, nan)

We take the soil properties for sand (first compartment) and clay (second compartment)
from table 1 of :cite:t:`ref-Lai2015`:

>>> residualmoisture(0.02, 0.09, nan)
>>> saturationmoisture(0.417, 0.385, nan)
>>> saturatedconductivity(235.6, 0.6, nan)
>>> poresizedistribution(0.694, 0.165, nan)
>>> airentrypotential(72.6, 373.0, nan)

Due to changing the arrays' shapes, we need to update the memorised initial conditions
required for checking the water balance:

>>> test.reset_inits()
>>> conditions = sequences.conditions

Sand allows for much more infiltration than clay, of course.  So, the wetting front
created during the first rainfall impulse reaches the sand soil's bottom (at a depth of
400 mm) during the 6th hour.  The tiny amount of percolation (0.0002 mm) at this time
is due to numerical inaccuracy (or the fact that |Merge_SoilDepthOvershootings_V1|
considers water overshooting the soil's depth as groundwater recharge).  In contrast,
in the clay soil, the deepest wetting front propagates to a depth of less than 70 mm
during the entire 24 h period only:

.. integration-test::

    >>> test("ga_garto_5h_3soils")
    |  date | rainfall | capillaryrise | evaporation |             surfacewatersupply |           soilwatersupply |           demand |                  infiltration |                percolation |           soilwateraddition |           withdrawal |                 surfacerunoff | totalinfiltration | totalpercolation | totalsoilwateraddition | totalwithdrawal | totalsurfacerunoff |                                                                                   moisture |                                                                               frontdepth |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |     40.0 |           0.0 |         1.0 | 40.0  40.0                40.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 | 40.0  14.791244           0.0 | 0.019062  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         1.0 | 0.0  24.279057           39.0 |         11.597081 |         0.003177 |                    0.0 |             1.0 |          27.593019 |      0.1  0.1  0.1  0.301056     0.385  0.1       0.1    0.1  0.1       0.1  0.1       0.1 | 400.0  100.0  0.0  193.881434  51.652432  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 01:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 |      0.1  0.1  0.1  0.230493  0.332214  0.1       0.1    0.1  0.1       0.1  0.1       0.1 | 400.0  100.0  0.0  291.056551  59.087523  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 02:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 |      0.1  0.1  0.1  0.209759  0.307931  0.1       0.1    0.1  0.1       0.1  0.1       0.1 | 400.0  100.0  0.0  336.929013   61.17858  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 03:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 |      0.1  0.1  0.1  0.197433  0.288756  0.1       0.1    0.1  0.1       0.1  0.1       0.1 | 400.0  100.0  0.0  369.288731  62.095805  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 04:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 |      0.1  0.1  0.1  0.188608  0.271453  0.1       0.1    0.1  0.1       0.1  0.1       0.1 | 400.0  100.0  0.0  394.781137  62.530085  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 05:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 | 0.000201  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |         0.000033 |                    0.0 |             0.5 |                0.0 | 0.184952  0.1  0.1  0.184953  0.254952  0.1  0.184953    0.1  0.1  0.184953  0.1       0.1 | 400.0  100.0  0.0         0.0  62.735058  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 06:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.182452  0.1  0.1  0.182453  0.238807  0.1  0.182453    0.1  0.1  0.182453  0.1       0.1 | 400.0  100.0  0.0         0.0   62.82789  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 07:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.179952  0.1  0.1  0.179953  0.222814  0.1  0.179953    0.1  0.1  0.179953  0.1       0.1 | 400.0  100.0  0.0         0.0  62.867167  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 08:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.177452  0.1  0.1  0.177453  0.206881  0.1  0.177453    0.1  0.1  0.177453  0.1       0.1 | 400.0  100.0  0.0         0.0  62.882303  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 09:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.174952  0.1  0.1  0.174953  0.190971  0.1  0.174953    0.1  0.1  0.174953  0.1       0.1 | 400.0  100.0  0.0         0.0  62.887463  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 10:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.172452  0.1  0.1  0.172453  0.175068  0.1  0.172453    0.1  0.1  0.172453  0.1       0.1 | 400.0  100.0  0.0         0.0   62.88896  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 11:00 |     15.0 |           0.0 |         1.0 | 15.0  15.0                15.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 | 15.0  11.882861           0.0 | 0.845942  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         1.0 | 0.0   2.520368           14.0 |          6.460954 |          0.14099 |                    0.0 |             1.0 |           7.840123 | 0.172452  0.1  0.1  0.247859  0.175068  0.1  0.172452  0.385  0.1  0.172452  0.1       0.1 | 400.0  100.0  0.0  174.440504   62.88896  0.0  0.0  54.682601  0.0  0.0  0.0         0.0 |
    | 12:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.172452  0.1  0.1  0.213064  0.336058  0.1  0.172452    0.1  0.1  0.172452  0.1       0.1 | 400.0  100.0  0.0  299.268379  64.393528  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 13:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.172452  0.1  0.1  0.200519  0.313074  0.1  0.172452    0.1  0.1  0.172452  0.1       0.1 | 400.0  100.0  0.0  397.400794  66.646073  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 14:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |  0.00029  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |         0.000048 |                    0.0 |             0.5 |                0.0 | 0.197836  0.1  0.1  0.197837  0.295007  0.1  0.197837    0.1  0.1  0.197837  0.1       0.1 | 400.0  100.0  0.0         0.0  67.692993  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 15:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.195336  0.1  0.1  0.195337  0.278839  0.1  0.195337    0.1  0.1  0.195337  0.1       0.1 | 400.0  100.0  0.0         0.0  68.220977  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 16:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.192836  0.1  0.1  0.192837  0.263536  0.1  0.192837    0.1  0.1  0.192837  0.1       0.1 | 400.0  100.0  0.0         0.0  68.489783  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 17:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.190336  0.1  0.1  0.190337  0.248646  0.1  0.190337    0.1  0.1  0.190337  0.1       0.1 | 400.0  100.0  0.0         0.0  68.623364  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 18:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.187836  0.1  0.1  0.187837   0.23395  0.1  0.187837    0.1  0.1  0.187837  0.1       0.1 | 400.0  100.0  0.0         0.0  68.686744  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 19:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.185336  0.1  0.1  0.185337  0.219342  0.1  0.185337    0.1  0.1  0.185337  0.1       0.1 | 400.0  100.0  0.0         0.0  68.714921  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 20:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.182836  0.1  0.1  0.182837  0.204772  0.1  0.182837    0.1  0.1  0.182837  0.1       0.1 | 400.0  100.0  0.0         0.0  68.726433  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 21:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.180336  0.1  0.1  0.180337  0.190216  0.1  0.180337    0.1  0.1  0.180337  0.1       0.1 | 400.0  100.0  0.0         0.0  68.730654  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 22:00 |      0.0 |           0.0 |         1.0 |  0.0   0.0                 0.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 |  0.0        0.0           0.0 |      0.0  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         0.0 | 0.0        0.0            0.0 |               0.0 |              0.0 |                    0.0 |             0.5 |                0.0 | 0.177836  0.1  0.1  0.177837  0.175665  0.1  0.177837    0.1  0.1  0.177837  0.1       0.1 | 400.0  100.0  0.0         0.0  68.731999  0.0  0.0        0.0  0.0  0.0  0.0         0.0 |
    | 23:00 |     15.0 |           0.0 |         1.0 | 15.0  15.0                15.0 | 0.0  0.0              0.0 | 1.0  1.0     1.0 | 15.0  11.870193           0.0 | 1.037538  0.0          0.0 | 0.0  0.0                0.0 | 1.0  1.0         1.0 | 0.0    2.53189           14.0 |          6.456731 |         0.172923 |                    0.0 |             1.0 |           7.843963 | 0.177836  0.1  0.1  0.247817  0.175665  0.1  0.177836  0.385  0.1  0.177836  0.1       0.1 | 400.0  100.0  0.0  185.229656     68.732  0.0  0.0   54.78341  0.0  0.0  0.0         0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core.typingtools import *

# ...from ga
from hydpy.models.ga import ga_model


class Model(modeltools.AdHocModel, ga_model.MixinGARTO):
    """The GARTO algorithm (assuming a hydrostatic groundwater table), implemented as
    a stand-alone model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        ga_model.Calc_SurfaceWaterSupply_V1,
        ga_model.Calc_SoilWaterSupply_V1,
        ga_model.Calc_Demand_V1,
        ga_model.Perform_GARTO_V1,
        ga_model.Calc_TotalInfiltration_V1,
        ga_model.Calc_TotalPercolation_V1,
        ga_model.Calc_TotalSoilWaterAddition_V1,
        ga_model.Calc_TotalWithdrawal_V1,
        ga_model.Calc_TotalSurfaceRunoff_V1,
    )
    ADD_METHODS = (
        ga_model.Return_RelativeMoisture_V1,
        ga_model.Return_Conductivity_V1,
        ga_model.Return_CapillaryDrive_V1,
        ga_model.Return_DryDepth_V1,
        ga_model.Return_LastActiveBin_V1,
        ga_model.Active_Bin_V1,
        ga_model.Percolate_FilledBin_V1,
        ga_model.Shift_Front_V1,
        ga_model.Redistribute_Front_V1,
        ga_model.Infiltrate_WettingFrontBins_V1,
        ga_model.Merge_FrontDepthOvershootings_V1,
        ga_model.Merge_SoilDepthOvershootings_V1,
        ga_model.Water_AllBins_V1,
        ga_model.Withdraw_AllBins_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
