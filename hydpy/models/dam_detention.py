# pylint: disable=line-too-long, unused-wildcard-import
"""|dam_detention| simulates the flood protection effects of dry detention basins that
actively control their release.

|dam_detention| serves similar purposes as |dam_lretention| but controls its outflow
actively according to "safe discharge" estimates, which are usually derived from
discharge values simulated (or measured) at other river segments.  Opposed to
|dam_lretention|, |dam_detention| requires no relationship between water level and
(possible) release, as it tries to release the ideal amount of water and neglects any
"natural" lake retention effects.  Due to this conceptual design, |dam_detention|
requires no numerical solution algorithms (like most other models in the HydPy-Dam
family) and is therefore solved analytically.

It is also possible to simulate wet basins by setting the |TargetVolume| parameter to a
value larger than one.  Note that even then, natural lake retention effects are
neglected, so |dam_lretention| or a similar model of the HydPy-Dam family might be
preferable.

The information for estimating the safe discharge is transmitted via an arbitrary
number of observer nodes.  Therefore, |dam_detention| can react as soon as critical
situations somewhere else in the river network occur.   Please note that an observer
node cannot be positioned downstream of the element that handles the observing
|dam_detention| instance.

Integration tests
=================

We perform all example calculations over a period of 20 days:

>>> from hydpy import Element, IntegrationTest, Node, pub
>>> pub.timegrids = "2000-01-01", "2000-01-21", "1d"

We prepare a |dam_detention| model instance:

>>> from hydpy.models.dam_detention import *
>>> parameterstep("1d")

We begin with the simplest case of a single inlet and a single outlet node and leave
the possibility of adding observer nodes for later consideration:

>>> inflow, outflow = Node("inflow"), Node("outflow")
>>> element = Element("element", inlets=inflow, outlets=outflow)
>>> element.model = model

The following test function instance facilitates the convenient execution of all
integration tests:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume

All integration tests shall start from dry initial conditions:

>>> test.inits = [(states.watervolume, 0.0), (logs.loggedadjustedevaporation, 0.0)]
>>> test.reset_inits()
>>> conditions = model.conditions

The following input time series stems from the integration tests on application model
|dam_lretention|:

>>> inflow.sequences.sim.series = [
...     0.0, 1.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
... ]

The first tests deal with a dry detention basin:

>>> targetvolume(0.0)
>>> maximumvolume(1.5)

As the surface area (which becomes relevant only after adding submodels that include
precipitation and evaporation into the water balance) is a fixed property, we set its
size to zero, which is the "regular" surface area of dry detention basins:

>>> surfacearea(0.0)

The following three parameters require values even if no corresponding submodels are
added (we plan to make this more convenient in the future):

>>> correctionprecipitation(1.0)
>>> correctionevaporation(1.0)
>>> weightevaporation(0.8)

The allowed release, which does not cause any harm directly downstream of the detention
basin, is 2 m³/s:

>>> allowedrelease(2.0)

As dry detention basins cannot help much in ensuring a minimum flow (e.g. for
ecological reasons), we set the minimum release to zero:

>>> minimumrelease(0.0)

We begin without any restrictions on the emptying speed:

>>> allowedwaterleveldrop(inf)

The following simple relationship between water volume and level does not affect the
basin's behaviour as long as |AllowedWaterLevelDrop| is set to infinity but enables
calculating the water level at the end of the respective simulation steps for
informational purposes:

>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0, 2.0], ys=[0.0, 1.0, 1.5]))

Parameter |Commission| allows for the modelling of the commissioning of a detention
basin during the simulation period.  We first set it to the start of the simulation
period, ensuring the detention basin is permanently active:

>>> commission("2000-01-01")

.. _dam_detention_local_protection:

local protection
________________

The current simple configuration shows the basic flood protection functionality of
|dam_detention|.  In this case, the protection is not perfect, but at least it reduces
the peak flow from 12 m³/s to less than 7 m³/s:

.. integration-test::

    >>> test("dam_detention_local_protection")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | saferelease | aimedrelease | unavoidablerelease |  outflow | watervolume | inflow |  outflow |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          1.0 |                0.0 |      1.0 |         0.0 |    1.0 |      1.0 |
    | 03.01. |     0.3456 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.3456 |    6.0 |      2.0 |
    | 04.01. |     1.1048 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   12.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.2096 |   12.0 |      2.0 |
    | 05.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   10.0 |         2.0 |          2.0 |           4.638889 | 6.638889 |         1.5 |   10.0 | 6.638889 |
    | 06.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |         2.0 |          2.0 |                4.0 |      6.0 |         1.5 |    6.0 |      6.0 |
    | 07.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |         2.0 |          2.0 |                1.0 |      3.0 |         1.5 |    3.0 |      3.0 |
    | 08.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |         2.0 |          2.0 |                0.0 |      2.0 |         1.5 |    2.0 |      2.0 |
    | 09.01. |     1.2068 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.4136 |    1.0 |      2.0 |
    | 10.01. |     1.1204 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.2408 |    0.0 |      2.0 |
    | 11.01. |      1.034 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |       1.068 |    0.0 |      2.0 |
    | 12.01. |     0.8952 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.8952 |    0.0 |      2.0 |
    | 13.01. |     0.7224 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.7224 |    0.0 |      2.0 |
    | 14.01. |     0.5496 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.5496 |    0.0 |      2.0 |
    | 15.01. |     0.3768 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.3768 |    0.0 |      2.0 |
    | 16.01. |      0.204 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |       0.204 |    0.0 |      2.0 |
    | 17.01. |     0.0312 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.0312 |    0.0 |      2.0 |
    | 18.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |     0.361111 |                0.0 | 0.361111 |         0.0 |    0.0 | 0.361111 |
    | 19.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 20.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |    0.0 |      0.0 |

There is no indication of an error in the water balance:

>>> from hydpy import round_
>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_detention_restricted_emptying:

restricted emptying
___________________

Setting the allowed water level drop to 0.15 m/day reduces the water release at the
later declining phase of the flood event (due to the higher water level decrease for
the same water volume decrease at this time):

.. integration-test::

    >>> allowedwaterleveldrop(0.15)
    >>> test("dam_detention_restricted_emptying")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | saferelease | aimedrelease | unavoidablerelease |  outflow | watervolume | inflow |  outflow |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          1.0 |                0.0 |      1.0 |         0.0 |    1.0 |      1.0 |
    | 03.01. |     0.3456 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.3456 |    6.0 |      2.0 |
    | 04.01. |     1.1048 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   12.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.2096 |   12.0 |      2.0 |
    | 05.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   10.0 |         2.0 |          2.0 |           4.638889 | 6.638889 |         1.5 |   10.0 | 6.638889 |
    | 06.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |         2.0 |          2.0 |                4.0 |      6.0 |         1.5 |    6.0 |      6.0 |
    | 07.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |         2.0 |          2.0 |                1.0 |      3.0 |         1.5 |    3.0 |      3.0 |
    | 08.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |         2.0 |          2.0 |                0.0 |      2.0 |         1.5 |    2.0 |      2.0 |
    | 09.01. |     1.2068 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.4136 |    1.0 |      2.0 |
    | 10.01. |     1.1204 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.2408 |    0.0 |      2.0 |
    | 11.01. |      1.034 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |       1.068 |    0.0 |      2.0 |
    | 12.01. |     0.8952 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.8952 |    0.0 |      2.0 |
    | 13.01. |     0.7452 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |     1.736111 |                0.0 | 1.736111 |      0.7452 |    0.0 | 1.736111 |
    | 14.01. |     0.5952 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |     1.736111 |                0.0 | 1.736111 |      0.5952 |    0.0 | 1.736111 |
    | 15.01. |     0.4452 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |     1.736111 |                0.0 | 1.736111 |      0.4452 |    0.0 | 1.736111 |
    | 16.01. |     0.2952 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |     1.736111 |                0.0 | 1.736111 |      0.2952 |    0.0 | 1.736111 |
    | 17.01. |     0.1452 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |     1.736111 |                0.0 | 1.736111 |      0.1452 |    0.0 | 1.736111 |
    | 18.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |     1.680556 |                0.0 | 1.680556 |         0.0 |    0.0 | 1.680556 |
    | 19.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 20.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |    0.0 |      0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_detention_remote_protection:

remote protection
_________________

We now add the observer node `gauge`, which provides discharge information from
somewhere else in the river network:

>>> gauge = Node("gauge")
>>> element.observers = gauge

Next, we add an |exch_interp| submodel that takes the observer node's discharge
information in converts it into a safe discharge estimate.  From 0 to 3 m³/s, this
estimate decreases linearly from 3 to 0 m³/s (and remains at 0 m³/s for larger values):

>>> nmbsafereleasemodels(1)
>>> with model.add_safereleasemodel("exch_interp", position=0):
...     observernodes("gauge")
...     x2y(PPoly.from_data(xs=[0.0, 3.0, 6.0], ys=[3.0, 0.0, 0.0]))

Due to the change in the network configuration, we need to recreate the test function
object:

>>> element.model.connect()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume
>>> test.inits = [(states.watervolume, 0.0), (logs.loggedadjustedevaporation, 0.0)]
>>> test.reset_inits()
>>> conditions = model.conditions

The inflow time series is initially identical to the one previously used but remains at
1 m³/s instead of decreasing to zero after the event:

>>> inflow.sequences.sim.series = [
...     0.0, 1.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 1.0,
...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
... ]

The observed discharge time also includes a runoff event, but this one occurs slightly
later in time:

>>> gauge.sequences.sim.series = [
...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
...     3.0, 6.0, 4.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
... ]


During the first days of the simulation period, the detention basin adjusts its
release, as in the previous examples, for local flood protection.   After that, it
reduces its release as much as possible to help decrease the flood at the remote
location (which does not work too well because there is still much water left from the
first event):

.. integration-test::

    >>> test("dam_detention_remote_protection")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | saferelease | aimedrelease | unavoidablerelease |  outflow | watervolume | gauge | inflow |  outflow |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |   1.0 |    0.0 |      0.0 |
    | 02.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          1.0 |                0.0 |      1.0 |         0.0 |   1.0 |    1.0 |      1.0 |
    | 03.01. |     0.3456 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.3456 |   1.0 |    6.0 |      2.0 |
    | 04.01. |     1.1048 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   12.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.2096 |   1.0 |   12.0 |      2.0 |
    | 05.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   10.0 |         2.0 |          2.0 |           4.638889 | 6.638889 |         1.5 |   1.0 |   10.0 | 6.638889 |
    | 06.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |         2.0 |          2.0 |                4.0 |      6.0 |         1.5 |   1.0 |    6.0 |      6.0 |
    | 07.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |         2.0 |          2.0 |                1.0 |      3.0 |         1.5 |   1.0 |    3.0 |      3.0 |
    | 08.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |         2.0 |          2.0 |                0.0 |      2.0 |         1.5 |   1.0 |    2.0 |      2.0 |
    | 09.01. |     1.2068 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.4136 |   1.0 |    1.0 |      2.0 |
    | 10.01. |     1.1636 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.3272 |   1.0 |    1.0 |      2.0 |
    | 11.01. |     1.2068 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         0.0 |          0.0 |                0.0 |      0.0 |      1.4136 |   3.0 |    1.0 |      0.0 |
    | 12.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         0.0 |          0.0 |                0.0 |      0.0 |         1.5 |   6.0 |    1.0 |      0.0 |
    | 13.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         0.0 |          0.0 |                1.0 |      1.0 |         1.5 |   4.0 |    1.0 |      1.0 |
    | 14.01. |       1.25 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         1.0 |          1.0 |                0.0 |      1.0 |         1.5 |   2.0 |    1.0 |      1.0 |
    | 15.01. |     1.2068 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.4136 |   1.0 |    1.0 |      2.0 |
    | 16.01. |     1.1636 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.3272 |   1.0 |    1.0 |      2.0 |
    | 17.01. |     1.1204 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.2408 |   1.0 |    1.0 |      2.0 |
    | 18.01. |     1.0772 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      1.1544 |   1.0 |    1.0 |      2.0 |
    | 19.01. |      1.034 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |       1.068 |   1.0 |    1.0 |      2.0 |
    | 20.01. |     0.9816 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |      0.9816 |   1.0 |    1.0 |      2.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_detention_target_volume:

target volume
_____________

This example demonstrates how |dam_detention| works for targeted water volumes larger
than zero:

>>> targetvolume(1.0)

Specifying a minimum release larger than zero now makes sense, as keeping the desired
water volume during wet periods may provide the opportunity to release additional water
in subsequent dry periods:

>>> minimumrelease(1.0)


The higher the targeted volume, the more reasonable it is to set the (time-averaged)
surface area size to a value larger than one:

>>> surfacearea(1.44)

With a non-zero surface area, adding submodels that introduce precipitation and
evaporation can make a relevant difference in the basin's water balance:

>>> with model.add_precipmodel_v2("meteo_precip_io") as precipmodel:
...     precipitationfactor(1.2)
...     inputs.precipitation.prepare_series()
...     inputs.precipitation.series = 0.0
...     inputs.precipitation.series[1] = 50.0
>>> with model.add_pemodel_v1("evap_ret_io") as pemodel:
...     evapotranspirationfactor(1.0)
...     inputs.referenceevapotranspiration.prepare_series()
...     inputs.referenceevapotranspiration.series = 6.0


We suppress the inflow directly after the event but reactivate it with 1.5 m³/s for the
last few simulation steps:

>>> inflow.sequences.sim.series[9:16] = 0.0
>>> inflow.sequences.sim.series[16:] = 1.5

As expected, |dam_detention| now keeps the targeted volume in flood-free periods as
long as the sum of inflow and precipitation exceeds the sum of evaporation and minimum
release:

.. integration-test::

    >>> test("dam_detention_target_volume")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | saferelease | aimedrelease | unavoidablerelease |  outflow | watervolume | gauge | inflow |  outflow |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  6.0 |                0.08 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |   1.0 |    0.0 |      0.0 |
    | 02.01. |   0.078106 |          60.0 |                   1.0 |                  6.0 |               0.096 |             0.096 |    1.0 |         2.0 |          1.0 |                0.0 |      1.0 |    0.078106 |   1.0 |    1.0 |      1.0 |
    | 03.01. |   0.501535 |           0.0 |                   0.0 |                  6.0 |              0.0992 |            0.0992 |    6.0 |         2.0 |          1.0 |                0.0 |      1.0 |    0.501535 |   1.0 |    6.0 |      1.0 |
    | 04.01. |   1.178454 |           0.0 |                   0.0 |                  6.0 |             0.09984 |           0.09984 |   12.0 |         2.0 |          2.0 |                0.0 |      2.0 |    1.356909 |   1.0 |   12.0 |      2.0 |
    | 05.01. |       1.25 |           0.0 |                   0.0 |                  6.0 |            0.099968 |          0.099968 |   10.0 |         2.0 |          2.0 |           6.243881 | 8.243881 |         1.5 |   1.0 |   10.0 | 8.243881 |
    | 06.01. |       1.25 |           0.0 |                   0.0 |                  6.0 |            0.099994 |          0.099994 |    6.0 |         2.0 |          2.0 |           3.900006 | 5.900006 |         1.5 |   1.0 |    6.0 | 5.900006 |
    | 07.01. |       1.25 |           0.0 |                   0.0 |                  6.0 |            0.099999 |          0.099999 |    3.0 |         2.0 |          2.0 |           0.900001 | 2.900001 |         1.5 |   1.0 |    3.0 | 2.900001 |
    | 08.01. |    1.24568 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    2.0 |         2.0 |          2.0 |                0.0 |      2.0 |     1.49136 |   1.0 |    2.0 |      2.0 |
    | 09.01. |    1.19816 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |     1.39632 |   1.0 |    1.0 |      2.0 |
    | 10.01. |    1.10744 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |     1.21488 |   1.0 |    0.0 |      2.0 |
    | 11.01. |    1.10312 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         0.0 |          0.0 |                0.0 |      0.0 |     1.20624 |   3.0 |    0.0 |      0.0 |
    | 12.01. |     1.0988 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         0.0 |          0.0 |                0.0 |      0.0 |      1.1976 |   6.0 |    0.0 |      0.0 |
    | 13.01. |    1.09448 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         0.0 |          0.0 |                0.0 |      0.0 |     1.18896 |   4.0 |    0.0 |      0.0 |
    | 14.01. |    1.04696 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         1.0 |          1.0 |                0.0 |      1.0 |     1.09392 |   2.0 |    0.0 |      1.0 |
    | 15.01. |    0.99888 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         2.0 |          1.0 |                0.0 |      1.0 |     0.99888 |   1.0 |    0.0 |      1.0 |
    | 16.01. |    0.90384 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         2.0 |          1.0 |                0.0 |      1.0 |     0.90384 |   1.0 |    0.0 |      1.0 |
    | 17.01. |     0.9384 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |          1.0 |                0.0 |      1.0 |      0.9384 |   1.0 |    1.5 |      1.0 |
    | 18.01. |    0.97296 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |          1.0 |                0.0 |      1.0 |     0.97296 |   1.0 |    1.5 |      1.0 |
    | 19.01. |        1.0 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |     1.087037 |                0.0 | 1.087037 |         1.0 |   1.0 |    1.5 | 1.087037 |
    | 20.01. |        1.0 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |          1.4 |                0.0 |      1.4 |         1.0 |   1.0 |    1.5 |      1.4 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_detention_commissioning:

commissioning
_____________

In this example, we set the commission date to the beginning of the fourth day of the
simulation period:

>>> commission("2000-01-04")

On the first three days, the model now passes its net input (consisting of inflow plus
precipitation minus evaporation) directly.  From the fourth day on, it switches to the
"normal" behaviour described above:

.. integration-test::

    >>> test("dam_detention_commissioning")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | saferelease | aimedrelease | unavoidablerelease |  outflow | watervolume | gauge | inflow |  outflow |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  6.0 |                0.08 |               0.0 |    0.0 |         2.0 |          0.0 |                0.0 |      0.0 |         0.0 |   1.0 |    0.0 |      0.0 |
    | 02.01. |        0.0 |          60.0 |                   1.0 |                  6.0 |               0.096 |             0.096 |    1.0 |         2.0 |          0.0 |              1.904 |    1.904 |         0.0 |   1.0 |    1.0 |    1.904 |
    | 03.01. |        0.0 |           0.0 |                   0.0 |                  6.0 |              0.0992 |            0.0992 |    6.0 |         2.0 |          0.0 |             5.9008 |   5.9008 |         0.0 |   1.0 |    6.0 |   5.9008 |
    | 04.01. |   0.941774 |           0.0 |                   0.0 |                  6.0 |             0.09984 |           0.09984 |   12.0 |         2.0 |          1.0 |                0.0 |      1.0 |    0.941774 |   1.0 |   12.0 |      1.0 |
    | 05.01. |       1.25 |           0.0 |                   0.0 |                  6.0 |            0.099968 |          0.099968 |   10.0 |         2.0 |          2.0 |           1.439081 | 3.439081 |         1.5 |   1.0 |   10.0 | 3.439081 |
    | 06.01. |       1.25 |           0.0 |                   0.0 |                  6.0 |            0.099994 |          0.099994 |    6.0 |         2.0 |          2.0 |           3.900006 | 5.900006 |         1.5 |   1.0 |    6.0 | 5.900006 |
    | 07.01. |       1.25 |           0.0 |                   0.0 |                  6.0 |            0.099999 |          0.099999 |    3.0 |         2.0 |          2.0 |           0.900001 | 2.900001 |         1.5 |   1.0 |    3.0 | 2.900001 |
    | 08.01. |    1.24568 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    2.0 |         2.0 |          2.0 |                0.0 |      2.0 |     1.49136 |   1.0 |    2.0 |      2.0 |
    | 09.01. |    1.19816 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.0 |         2.0 |          2.0 |                0.0 |      2.0 |     1.39632 |   1.0 |    1.0 |      2.0 |
    | 10.01. |    1.10744 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         2.0 |          2.0 |                0.0 |      2.0 |     1.21488 |   1.0 |    0.0 |      2.0 |
    | 11.01. |    1.10312 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         0.0 |          0.0 |                0.0 |      0.0 |     1.20624 |   3.0 |    0.0 |      0.0 |
    | 12.01. |     1.0988 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         0.0 |          0.0 |                0.0 |      0.0 |      1.1976 |   6.0 |    0.0 |      0.0 |
    | 13.01. |    1.09448 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         0.0 |          0.0 |                0.0 |      0.0 |     1.18896 |   4.0 |    0.0 |      0.0 |
    | 14.01. |    1.04696 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         1.0 |          1.0 |                0.0 |      1.0 |     1.09392 |   2.0 |    0.0 |      1.0 |
    | 15.01. |    0.99888 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         2.0 |          1.0 |                0.0 |      1.0 |     0.99888 |   1.0 |    0.0 |      1.0 |
    | 16.01. |    0.90384 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    0.0 |         2.0 |          1.0 |                0.0 |      1.0 |     0.90384 |   1.0 |    0.0 |      1.0 |
    | 17.01. |     0.9384 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |          1.0 |                0.0 |      1.0 |      0.9384 |   1.0 |    1.5 |      1.0 |
    | 18.01. |    0.97296 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |          1.0 |                0.0 |      1.0 |     0.97296 |   1.0 |    1.5 |      1.0 |
    | 19.01. |        1.0 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |     1.087037 |                0.0 | 1.087037 |         1.0 |   1.0 |    1.5 | 1.087037 |
    | 20.01. |        1.0 |           0.0 |                   0.0 |                  6.0 |                 0.1 |               0.1 |    1.5 |         2.0 |          1.4 |                0.0 |      1.4 |         1.0 |   1.0 |    1.5 |      1.4 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.exe.modelimports import *
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.interfaces import exchangeinterfaces
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces

# ...from dam
from hydpy.models.dam import dam_model


class Model(
    modeltools.AdHocModel,
    dam_model.MixinSimpleWaterBalance,
    dam_model.Main_PrecipModel_V2,
    dam_model.Main_PEModel_V1,
    exchangeinterfaces.ExchangeModel_V1,
):
    """|dam_detention.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Dam-DB", description="detention basin model")
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (dam_model.Pick_Inflow_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        dam_model.Calc_Precipitation_V1,
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Calc_PotentialEvaporation_V1,
        dam_model.Calc_AdjustedEvaporation_V1,
        dam_model.Calc_AllowedWaterLevel_V1,
        dam_model.Calc_AllowedDischarge_V3,
        dam_model.Update_WaterVolume_V5,
        dam_model.Calc_ActualEvaporation_WaterVolume_V1,
        dam_model.Calc_SafeRelease_V1,
        dam_model.Calc_AimedRelease_WaterVolume_V1,
        dam_model.Calc_UnavoidableRelease_WaterVolume_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_Outflow_V6,
    )
    ADD_METHODS = (dam_model.Return_WaterLevelError_V1,)
    OUTLET_METHODS = (dam_model.Pass_Outflow_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        precipinterfaces.PrecipModel_V2,
        petinterfaces.PETModel_V1,
        exchangeinterfaces.ExchangeModel_V1,
    )
    SUBMODELS = (dam_model.PegasusWaterVolume,)

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)

    safereleasemodels = modeltools.SubmodelsProperty(
        exchangeinterfaces.ExchangeModel_V1
    )

    @importtools.prepare_submodel(
        "safereleasemodels", exchangeinterfaces.ExchangeModel_V1, dimensionality=l1
    )
    def add_safereleasemodel(
        self,
        safereleasemodel: exchangeinterfaces.ExchangeModel_V1,
        *,
        position: int,
        refresh: bool,
    ) -> None:
        """Initialise the given `safereleasemodel` that follows the |ExchangeModel_V1|
        interface."""


tester = Tester()
cythonizer = Cythonizer()
