# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Version 3 of HydPy-Dam.

|dam_v003| is quite similar to |dam_v002|.  Both application models provide the same
flood retentions functionalities.  Also, both try to meet the water demand at a remote
location.  The difference is that |dam_v002| expects this demand to occur in the channel
downstream (usually to increase low discharge values).  Instead, |dam_v003| supplies
water to a different location (such as a drinking water treatment plant). Hence
|dam_v002| releases its water via a single output path while |dam_v003| divides it into
two separate paths.

The following explanations focus on this difference.  For further information on using
|dam_v003|, please read the documentation on |dam_v001| and |dam_v002|.

Integration tests
=================

.. how_to_understand_integration_tests::

To illustrate the functionalities of |dam_v003|, we refer back to those examples of
the comprehensive documentation on application model |dam_v001| we also revisited when
discussing |dam_v002|.  In contrast to the comparison between |dam_v001| and
|dam_v002|, we cannot define settings for |dam_v003| that lead to identical results
in cases of remote demand.  In all other situations, |dam_v003| works like |dam_v001|
and |dam_v002|.  Hence, most examples serve more to confirm the correctness of the
model's implementation than explaining new features.

The time-related setup is identical to the ones of |dam_v001| and |dam_v002|:

>>> from hydpy import pub, Node, Element
>>> pub.timegrids = "01.01.2000", "21.01.2000", "1d"

|dam_v003| requires connections to four instead of three |Node| objects.  Instead of
one outlet node, there must be two outlet nodes.  Node `outflow` corresponds to the
`outflow` node of the documentation on |dam_v001| and |dam_v002| and passes the received
outflow into the channel immediately downstream the dam.  Node `actual_supply` is new
and serves for supplying a different location with water.  Node `required_supply` is
equivalent to node `demand` of the documentation on |dam_v002|.  It delivers the same
information but from a different location:

>>> inflow = Node("inflow", variable="Q")
>>> outflow = Node("outflow", variable="Q")
>>> actual_supply = Node("actual_supply", variable="S")
>>> required_supply = Node("required_supply", variable="S")
>>> dam = Element("dam",
...               inlets=inflow,
...               outlets=(outflow, actual_supply),
...               receivers=required_supply)
>>> from hydpy.models.dam_v003 import *
>>> parameterstep("1d")
>>> dam.model = model

|dam_v001| releases water via two outlet sequences, |dam_outlets.Q| and |dam_outlets.S|,
and needs to know which one corresponds to which outlet node.  It gathers this
information when building the connection with its |Element| object `dam` in the last
assignment above.  Therefore, it inspects the |Node.variable| attribute of each outlet
node.  In our example, we use the string literals "Q" and "S" to enable the correct
allocation.  See the documentation on method |Model.connect| for alternatives and more
detailed explanations.

We define the configuration of the |IntegrationTest| object, the initial conditions,
the input time series, and the parameter values exactly as for |dam_v002|:

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(dam)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume

>>> test.inits=((states.watervolume, 0.0),
...             (logs.loggedadjustedevaporation, 0.0),
...             (logs.loggedrequiredremoterelease, 0.005))

>>> inflow.sequences.sim.series = 1.0
>>> inputs.precipitation.series = 0.0
>>> inputs.evaporation.series = 0.0

>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 0.25]))
>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0], ys=[0.0]))
>>> catchmentarea(86.4)
>>> neardischargeminimumthreshold(0.2)
>>> neardischargeminimumtolerance(0.2)
>>> waterlevelminimumthreshold(0.0)
>>> waterlevelminimumtolerance(0.0)
>>> restricttargetedrelease(True)
>>> surfacearea(1.44)
>>> correctionprecipitation(1.2)
>>> correctionevaporation(1.2)
>>> weightevaporation(0.8)
>>> thresholdevaporation(0.0)
>>> toleranceevaporation(0.001)

Now, we prepare the two additional parameters, |WaterLevelMinimumRemoteThreshold| and
|WaterLevelMinimumRemoteTolerance|:

>>> waterlevelminimumremotethreshold(0.0)
>>> waterlevelminimumremotetolerance(0.0)

.. _dam_v003_smooth_near_minimum:

smooth near minimum
___________________

This example corresponds to the :ref:`dam_v001_smooth_near_minimum` example of
application model |dam_v001| and the :ref:`dam_v002_smooth_near_minimum` example of
application model |dam_v002|.  We again use the same remote demand:

>>> required_supply.sequences.sim.series = [
...     0.008588, 0.010053, 0.013858, 0.027322, 0.064075, 0.235523, 0.470414,
...     0.735001, 0.891263, 0.696325, 0.349797, 0.105231, 0.111928, 0.240436,
...     0.229369, 0.058622, 0.016958, 0.008447, 0.004155, 0.0]

Due to the separate output paths, there are relevant differences to the results of
|dam_v001| and |dam_v002|.  |dam_v001| and |dam_v002| can use the same water to both
meet the near and the remote demand, which is not possible for |dam_v003|.  Hence, it
must release a larger total amount of water:

.. integration-test::

    >>> test("dam_v003_smooth_near_minimum")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply | inflow |  outflow | required_supply |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017356 |                   0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 |      0.004792 |    1.0 | 0.191667 |        0.008588 |
    | 02.01. |           0.0 |         0.0 |   0.034451 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008588 |             0.2 |             0.2 |           0.2 |            0.008588 |            0.0 |      0.2 |    0.137804 |      0.008588 |    1.0 |      0.2 |        0.010053 |
    | 03.01. |           0.0 |         0.0 |   0.051514 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.010053 |             0.2 |             0.2 |           0.2 |            0.010053 |            0.0 |      0.2 |    0.206055 |      0.010053 |    1.0 |      0.2 |        0.013858 |
    | 04.01. |           0.0 |         0.0 |   0.068495 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.013858 |             0.2 |             0.2 |           0.2 |            0.013858 |            0.0 |      0.2 |    0.273978 |      0.013858 |    1.0 |      0.2 |        0.027322 |
    | 05.01. |           0.0 |         0.0 |   0.085184 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.027322 |             0.2 |             0.2 |           0.2 |            0.027322 |            0.0 |      0.2 |    0.340737 |      0.027322 |    1.0 |      0.2 |        0.064075 |
    | 06.01. |           0.0 |         0.0 |    0.10108 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.064075 |             0.2 |             0.2 |           0.2 |            0.064075 |            0.0 |      0.2 |    0.404321 |      0.064075 |    1.0 |      0.2 |        0.235523 |
    | 07.01. |           0.0 |         0.0 |   0.113273 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.235523 |             0.2 |             0.2 |           0.2 |            0.235523 |            0.0 |      0.2 |    0.453092 |      0.235523 |    1.0 |      0.2 |        0.470414 |
    | 08.01. |           0.0 |         0.0 |   0.120392 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.470414 |             0.2 |             0.2 |           0.2 |            0.470414 |            0.0 |      0.2 |    0.481568 |      0.470414 |    1.0 |      0.2 |        0.735001 |
    | 09.01. |           0.0 |         0.0 |   0.121796 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.735001 |             0.2 |             0.2 |           0.2 |            0.735001 |            0.0 |      0.2 |    0.487184 |      0.735001 |    1.0 |      0.2 |        0.891263 |
    | 10.01. |           0.0 |         0.0 |   0.119825 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.891263 |             0.2 |             0.2 |           0.2 |            0.891263 |            0.0 |      0.2 |    0.479299 |      0.891263 |    1.0 |      0.2 |        0.696325 |
    | 11.01. |           0.0 |         0.0 |   0.122064 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.696325 |             0.2 |             0.2 |           0.2 |            0.696325 |            0.0 |      0.2 |    0.488257 |      0.696325 |    1.0 |      0.2 |        0.349797 |
    | 12.01. |           0.0 |         0.0 |   0.131789 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.349797 |             0.2 |             0.2 |           0.2 |            0.349797 |            0.0 |      0.2 |    0.527154 |      0.349797 |    1.0 |      0.2 |        0.105231 |
    | 13.01. |           0.0 |         0.0 |   0.146796 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.105231 |             0.2 |             0.2 |           0.2 |            0.105231 |            0.0 |      0.2 |    0.587182 |      0.105231 |    1.0 |      0.2 |        0.111928 |
    | 14.01. |           0.0 |         0.0 |   0.161658 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.111928 |             0.2 |             0.2 |           0.2 |            0.111928 |            0.0 |      0.2 |    0.646632 |      0.111928 |    1.0 |      0.2 |        0.240436 |
    | 15.01. |           0.0 |         0.0 |   0.173745 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.240436 |             0.2 |             0.2 |           0.2 |            0.240436 |            0.0 |      0.2 |    0.694978 |      0.240436 |    1.0 |      0.2 |        0.229369 |
    | 16.01. |           0.0 |         0.0 |    0.18607 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.229369 |             0.2 |             0.2 |           0.2 |            0.229369 |            0.0 |      0.2 |    0.744281 |      0.229369 |    1.0 |      0.2 |        0.058622 |
    | 17.01. |           0.0 |         0.0 |   0.202084 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.058622 |             0.2 |             0.2 |           0.2 |            0.058622 |            0.0 |      0.2 |    0.808336 |      0.058622 |    1.0 |      0.2 |        0.016958 |
    | 18.01. |           0.0 |         0.0 |   0.218998 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.016958 |             0.2 |             0.2 |           0.2 |            0.016958 |            0.0 |      0.2 |     0.87599 |      0.016958 |    1.0 |      0.2 |        0.008447 |
    | 19.01. |           0.0 |         0.0 |   0.236095 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008447 |             0.2 |             0.2 |           0.2 |            0.008447 |            0.0 |      0.2 |    0.944381 |      0.008447 |    1.0 |      0.2 |        0.004155 |
    | 20.01. |           0.0 |         0.0 |   0.253285 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.004155 |             0.2 |             0.2 |           0.2 |            0.004155 |            0.0 |      0.2 |    1.013142 |      0.004155 |    1.0 |      0.2 |             0.0 |

.. _dam_v003_restriction_enabled:

restriction enabled
___________________

This example corresponds to the :ref:`dam_v001_restriction_enabled` example of
application model |dam_v001| and the :ref:`dam_v002_restriction_enabled` example of
application model |dam_v002|.  We update the time series of the inflow and the required
remote release accordingly:

>>> inflow.sequences.sim.series[10:] = 0.1
>>> required_supply.sequences.sim.series = [
...     0.008746, 0.010632, 0.015099, 0.03006, 0.068641, 0.242578, 0.474285,
...     0.784512, 0.95036, 0.35, 0.034564, 0.299482, 0.585979, 0.557422,
...     0.229369, 0.142578, 0.068641, 0.029844, 0.012348, 0.0]
>>> neardischargeminimumtolerance(0.0)

The results show that the restriction on releasing water during low inflow conditions
concerns the release into the channel downstream only:

.. integration-test::

    >>> test("dam_v003_restriction_enabled")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply | inflow |  outflow | required_supply |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017357 |                   0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 |      0.004792 |    1.0 | 0.191667 |        0.008746 |
    | 02.01. |           0.0 |         0.0 |   0.034448 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008746 |             0.2 |             0.2 |           0.2 |            0.008746 |            0.0 |      0.2 |     0.13779 |      0.008746 |    1.0 |      0.2 |        0.010632 |
    | 03.01. |           0.0 |         0.0 |   0.051498 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.010632 |             0.2 |             0.2 |           0.2 |            0.010632 |            0.0 |      0.2 |    0.205992 |      0.010632 |    1.0 |      0.2 |        0.015099 |
    | 04.01. |           0.0 |         0.0 |   0.068452 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.015099 |             0.2 |             0.2 |           0.2 |            0.015099 |            0.0 |      0.2 |    0.273807 |      0.015099 |    1.0 |      0.2 |         0.03006 |
    | 05.01. |           0.0 |         0.0 |   0.085083 |                   0.0 |                 0.0 |               0.0 |    1.0 |               0.03006 |             0.2 |             0.2 |           0.2 |             0.03006 |            0.0 |      0.2 |     0.34033 |       0.03006 |    1.0 |      0.2 |        0.068641 |
    | 06.01. |           0.0 |         0.0 |    0.10088 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.068641 |             0.2 |             0.2 |           0.2 |            0.068641 |            0.0 |      0.2 |    0.403519 |      0.068641 |    1.0 |      0.2 |        0.242578 |
    | 07.01. |           0.0 |         0.0 |    0.11292 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.242578 |             0.2 |             0.2 |           0.2 |            0.242578 |            0.0 |      0.2 |    0.451681 |      0.242578 |    1.0 |      0.2 |        0.474285 |
    | 08.01. |           0.0 |         0.0 |   0.119956 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.474285 |             0.2 |             0.2 |           0.2 |            0.474285 |            0.0 |      0.2 |    0.479822 |      0.474285 |    1.0 |      0.2 |        0.784512 |
    | 09.01. |           0.0 |         0.0 |    0.12029 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.784512 |             0.2 |             0.2 |           0.2 |            0.784512 |            0.0 |      0.2 |    0.481161 |      0.784512 |    1.0 |      0.2 |         0.95036 |
    | 10.01. |           0.0 |         0.0 |   0.117042 |                   0.0 |                 0.0 |               0.0 |    1.0 |               0.95036 |             0.2 |             0.2 |           0.2 |             0.95036 |            0.0 |      0.2 |     0.46817 |       0.95036 |    1.0 |      0.2 |            0.35 |
    | 11.01. |           0.0 |         0.0 |   0.109482 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  0.35 |             0.2 |             0.1 |           0.1 |                0.35 |            0.0 |      0.1 |     0.43793 |          0.35 |    0.1 |      0.1 |        0.034564 |
    | 12.01. |           0.0 |         0.0 |   0.108736 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.034564 |             0.2 |             0.1 |           0.1 |            0.034564 |            0.0 |      0.1 |    0.434943 |      0.034564 |    0.1 |      0.1 |        0.299482 |
    | 13.01. |           0.0 |         0.0 |   0.102267 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.299482 |             0.2 |             0.1 |           0.1 |            0.299482 |            0.0 |      0.1 |    0.409068 |      0.299482 |    0.1 |      0.1 |        0.585979 |
    | 14.01. |           0.0 |         0.0 |    0.08961 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.585979 |             0.2 |             0.1 |           0.1 |            0.585979 |            0.0 |      0.1 |    0.358439 |      0.585979 |    0.1 |      0.1 |        0.557422 |
    | 15.01. |           0.0 |         0.0 |    0.07757 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.557422 |             0.2 |             0.1 |           0.1 |            0.557422 |            0.0 |      0.1 |    0.310278 |      0.557422 |    0.1 |      0.1 |        0.229369 |
    | 16.01. |           0.0 |         0.0 |   0.072615 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.229369 |             0.2 |             0.1 |           0.1 |            0.229369 |            0.0 |      0.1 |    0.290461 |      0.229369 |    0.1 |      0.1 |        0.142578 |
    | 17.01. |           0.0 |         0.0 |   0.069535 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.142578 |             0.2 |             0.1 |           0.1 |            0.142578 |            0.0 |      0.1 |    0.278142 |      0.142578 |    0.1 |      0.1 |        0.068641 |
    | 18.01. |           0.0 |         0.0 |   0.068053 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.068641 |             0.2 |             0.1 |           0.1 |            0.068641 |            0.0 |      0.1 |    0.272211 |      0.068641 |    0.1 |      0.1 |        0.029844 |
    | 19.01. |           0.0 |         0.0 |   0.067408 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.029844 |             0.2 |             0.1 |           0.1 |            0.029844 |            0.0 |      0.1 |    0.269633 |      0.029844 |    0.1 |      0.1 |        0.012348 |
    | 20.01. |           0.0 |         0.0 |   0.067141 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.012348 |             0.2 |             0.1 |           0.1 |            0.012348 |            0.0 |      0.1 |    0.268566 |      0.012348 |    0.1 |      0.1 |             0.0 |

.. _dam_v003_smooth_stage_minimum:

smooth stage minimum
____________________

This example corresponds to the :ref:`dam_v001_smooth_stage_minimum` example of
application model |dam_v001| and the :ref:`dam_v002_smooth_stage_minimum` example of
application model |dam_v002|.  We update parameters |WaterLevelMinimumThreshold| and
|WaterLevelMinimumTolerance|, as well as the time series of the inflow and the required
remote release, accordingly, but keep the old value of |NearDischargeMinimumThreshold|:

>>> waterlevelminimumtolerance(0.01)
>>> waterlevelminimumthreshold(0.005)
>>> inflow.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)
>>> required_supply.sequences.sim.series = [
...     0.01232, 0.029323, 0.064084, 0.120198, 0.247367, 0.45567, 0.608464,
...     0.537314, 0.629775, 0.744091, 0.82219, 0.841916, 0.701812, 0.533258,
...     0.351863, 0.185207, 0.107697, 0.055458, 0.025948, 0.0]
>>> neardischargeminimumthreshold
neardischargeminimumthreshold(0.2)

Additionally, we illustrate the control parameters unknown to |dam_v001| and |dam_v002|,
|WaterLevelMinimumRemoteThreshold| and |WaterLevelMinimumRemoteTolerance|.  Separate
water level-related threshold values for the near demand (|WaterLevelMinimumThreshold|)
and the remote demand (|WaterLevelMinimumRemoteThreshold|) and their smoothing
parameters allows for a distinct configuration of both output paths in situations when
the available storage is limited.  Here, we set |WaterLevelMinimumRemoteThreshold| to a
higher value than |WaterLevelMinimumThreshold|.  Hence, the release into the channel
downstream has priority over the supply to the remote location:

>>> waterlevelminimumremotetolerance(0.01)
>>> waterlevelminimumremotethreshold(0.01)

.. integration-test::

    >>> test("dam_v003_smooth_stage_minimum")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply |   inflow |  outflow | required_supply |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.003486 |                   0.0 |                 0.0 |               0.0 |      0.2 |                 0.005 |             0.2 |             0.2 |      0.038491 |             0.00012 |            0.0 | 0.038491 |    0.013944 |       0.00012 |      0.2 | 0.038491 |         0.01232 |
    | 02.01. |           0.0 |         0.0 |   0.005678 |                   0.0 |                 0.0 |               0.0 | 0.189474 |               0.01232 |             0.2 |        0.189474 |      0.086988 |            0.000993 |            0.0 | 0.086988 |    0.022713 |      0.000993 | 0.189474 | 0.086988 |        0.029323 |
    | 03.01. |           0.0 |         0.0 |   0.006935 |                   0.0 |                 0.0 |               0.0 | 0.178947 |              0.029323 |             0.2 |        0.178947 |      0.116103 |            0.004642 |            0.0 | 0.116103 |    0.027742 |      0.004642 | 0.178947 | 0.116103 |        0.064084 |
    | 04.01. |           0.0 |         0.0 |   0.007554 |                   0.0 |                 0.0 |               0.0 | 0.168421 |              0.064084 |             0.2 |        0.168421 |      0.125159 |            0.014625 |            0.0 | 0.125159 |    0.030216 |      0.014625 | 0.168421 | 0.125159 |        0.120198 |
    | 05.01. |           0.0 |         0.0 |    0.00768 |                   0.0 |                 0.0 |               0.0 | 0.157895 |              0.120198 |             0.2 |        0.157895 |      0.121681 |            0.030361 |            0.0 | 0.121681 |    0.030722 |      0.030361 | 0.157895 | 0.121681 |        0.247367 |
    | 06.01. |           0.0 |         0.0 |   0.007261 |                   0.0 |                 0.0 |               0.0 | 0.147368 |              0.247367 |             0.2 |        0.147368 |      0.109923 |            0.056857 |            0.0 | 0.109923 |    0.029044 |      0.056857 | 0.147368 | 0.109923 |         0.45567 |
    | 07.01. |           0.0 |         0.0 |   0.006338 |                   0.0 |                 0.0 |               0.0 | 0.136842 |               0.45567 |             0.2 |        0.136842 |      0.094858 |            0.084715 |            0.0 | 0.094858 |    0.025352 |      0.084715 | 0.136842 | 0.094858 |        0.608464 |
    | 08.01. |           0.0 |         0.0 |   0.005622 |                   0.0 |                 0.0 |               0.0 | 0.126316 |              0.608464 |             0.2 |        0.126316 |      0.076914 |            0.082553 |            0.0 | 0.076914 |    0.022488 |      0.082553 | 0.126316 | 0.076914 |        0.537314 |
    | 09.01. |           0.0 |         0.0 |   0.005446 |                   0.0 |                 0.0 |               0.0 | 0.115789 |              0.537314 |             0.2 |        0.115789 |      0.064167 |            0.059779 |            0.0 | 0.064167 |    0.021783 |      0.059779 | 0.115789 | 0.064167 |        0.629775 |
    | 10.01. |           0.0 |         0.0 |   0.005167 |                   0.0 |                 0.0 |               0.0 | 0.105263 |              0.629775 |             0.2 |        0.105263 |      0.055154 |            0.063011 |            0.0 | 0.055154 |    0.020669 |      0.063011 | 0.105263 | 0.055154 |        0.744091 |
    | 11.01. |           0.0 |         0.0 |   0.004819 |                   0.0 |                 0.0 |               0.0 | 0.094737 |              0.744091 |             0.2 |        0.094737 |      0.045986 |            0.064865 |            0.0 | 0.045986 |    0.019277 |      0.064865 | 0.094737 | 0.045986 |         0.82219 |
    | 12.01. |           0.0 |         0.0 |   0.004479 |                   0.0 |                 0.0 |               0.0 | 0.084211 |               0.82219 |             0.2 |        0.084211 |      0.037699 |             0.06228 |            0.0 | 0.037699 |    0.017914 |       0.06228 | 0.084211 | 0.037699 |        0.841916 |
    | 13.01. |           0.0 |         0.0 |   0.004191 |                   0.0 |                 0.0 |               0.0 | 0.073684 |              0.841916 |             0.2 |        0.073684 |      0.030632 |            0.056377 |            0.0 | 0.030632 |    0.016763 |      0.056377 | 0.073684 | 0.030632 |        0.701812 |
    | 14.01. |           0.0 |         0.0 |   0.004065 |                   0.0 |                 0.0 |               0.0 | 0.063158 |              0.701812 |             0.2 |        0.063158 |      0.025166 |            0.043828 |            0.0 | 0.025166 |    0.016259 |      0.043828 | 0.063158 | 0.025166 |        0.533258 |
    | 15.01. |           0.0 |         0.0 |    0.00405 |                   0.0 |                 0.0 |               0.0 | 0.052632 |              0.533258 |             0.2 |        0.052632 |      0.020693 |            0.032602 |            0.0 | 0.020693 |    0.016201 |      0.032602 | 0.052632 | 0.020693 |        0.351863 |
    | 16.01. |           0.0 |         0.0 |   0.004126 |                   0.0 |                 0.0 |               0.0 | 0.042105 |              0.351863 |             0.2 |        0.042105 |      0.016736 |            0.021882 |            0.0 | 0.016736 |    0.016502 |      0.021882 | 0.042105 | 0.016736 |        0.185207 |
    | 17.01. |           0.0 |         0.0 |   0.004268 |                   0.0 |                 0.0 |               0.0 | 0.031579 |              0.185207 |             0.2 |        0.031579 |      0.012934 |            0.012076 |            0.0 | 0.012934 |     0.01707 |      0.012076 | 0.031579 | 0.012934 |        0.107697 |
    | 18.01. |           0.0 |         0.0 |    0.00437 |                   0.0 |                 0.0 |               0.0 | 0.021053 |              0.107697 |             0.2 |        0.021053 |      0.008901 |            0.007386 |            0.0 | 0.008901 |    0.017482 |      0.007386 | 0.021053 | 0.008901 |        0.055458 |
    | 19.01. |           0.0 |         0.0 |   0.004415 |                   0.0 |                 0.0 |               0.0 | 0.010526 |              0.055458 |             0.2 |        0.010526 |      0.004535 |             0.00392 |            0.0 | 0.004535 |    0.017661 |       0.00392 | 0.010526 | 0.004535 |        0.025948 |
    | 20.01. |           0.0 |         0.0 |   0.004376 |                   0.0 |                 0.0 |               0.0 |      0.0 |              0.025948 |             0.2 |             0.0 |           0.0 |            0.001835 |            0.0 |      0.0 |    0.017502 |      0.001835 |      0.0 |      0.0 |             0.0 |

.. _dam_v003_evaporation:

evaporation
___________

This example corresponds to the :ref:`dam_v001_evaporation` example of application model
|dam_v001| and the :ref:`dam_v002_evaporation` example of application model |dam_v002|.
We update the time series of potential evaporation and the required remote release
accordingly:

>>> inputs.evaporation.series = 10 * [1.0] + 10 * [5.0]
>>> required_supply.sequences.sim.series = [
...     0.012321, 0.029352, 0.064305, 0.120897, 0.248435, 0.453671, 0.585089,
...     0.550583, 0.694398, 0.784979, 0.81852, 0.840207, 0.72592, 0.575373,
...     0.386003, 0.198088, 0.113577, 0.05798, 0.026921, 0.0]

Due to the remaining differences regarding remote demand, the following results differ
from those of |dam_v001| and |dam_v002|.  However, detailed comparisons show the same
patterns for adjusting given potential evaporation and its conversion to actual
evaporation under water scarcity:

.. integration-test::

    >>> test("dam_v003_evaporation")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply |   inflow |  outflow | required_supply |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         1.0 |   0.003204 |                   0.0 |               0.016 |          0.014663 |      0.2 |                 0.005 |             0.2 |             0.2 |      0.036881 |            0.000114 |            0.0 | 0.036881 |    0.012817 |      0.000114 |      0.2 | 0.036881 |        0.012321 |
    | 02.01. |           0.0 |         1.0 |   0.005171 |                   0.0 |              0.0192 |            0.0192 | 0.189474 |              0.012321 |             0.2 |        0.189474 |      0.078396 |            0.000832 |            0.0 | 0.078396 |    0.020683 |      0.000832 | 0.189474 | 0.078396 |        0.029352 |
    | 03.01. |           0.0 |         1.0 |   0.006267 |                   0.0 |             0.01984 |           0.01984 | 0.178947 |              0.029352 |             0.2 |        0.178947 |      0.104667 |             0.00367 |            0.0 | 0.104667 |     0.02507 |       0.00367 | 0.178947 | 0.104667 |        0.064305 |
    | 04.01. |           0.0 |         1.0 |   0.006777 |                   0.0 |            0.019968 |          0.019968 | 0.168421 |              0.064305 |             0.2 |        0.168421 |      0.113657 |            0.011204 |            0.0 | 0.113657 |    0.027108 |      0.011204 | 0.168421 | 0.113657 |        0.120897 |
    | 05.01. |           0.0 |         1.0 |   0.006873 |                   0.0 |            0.019994 |          0.019994 | 0.157895 |              0.120897 |             0.2 |        0.157895 |      0.110489 |            0.022953 |            0.0 | 0.110489 |    0.027493 |      0.022953 | 0.157895 | 0.110489 |        0.248435 |
    | 06.01. |           0.0 |         1.0 |   0.006531 |                   0.0 |            0.019999 |          0.019999 | 0.147368 |              0.248435 |             0.2 |        0.147368 |      0.099756 |            0.043467 |            0.0 | 0.099756 |    0.026124 |      0.043467 | 0.147368 | 0.099756 |        0.453671 |
    | 07.01. |           0.0 |         1.0 |   0.005779 |                   0.0 |                0.02 |              0.02 | 0.136842 |              0.453671 |             0.2 |        0.136842 |      0.085828 |            0.065832 |            0.0 | 0.085828 |    0.023115 |      0.065832 | 0.136842 | 0.085828 |        0.585089 |
    | 08.01. |           0.0 |         1.0 |   0.005171 |                   0.0 |                0.02 |              0.02 | 0.126316 |              0.585089 |             0.2 |        0.126316 |      0.069773 |            0.064688 |            0.0 | 0.069773 |    0.020684 |      0.064688 | 0.126316 | 0.069773 |        0.550583 |
    | 09.01. |           0.0 |         1.0 |    0.00492 |                   0.0 |                0.02 |              0.02 | 0.115789 |              0.550583 |             0.2 |        0.115789 |      0.057531 |            0.049863 |            0.0 | 0.057531 |    0.019681 |      0.049863 | 0.115789 | 0.057531 |        0.694398 |
    | 10.01. |           0.0 |         1.0 |   0.004547 |                   0.0 |                0.02 |              0.02 | 0.105263 |              0.694398 |             0.2 |        0.105263 |      0.048078 |            0.054461 |            0.0 | 0.048078 |    0.018189 |      0.054461 | 0.105263 | 0.048078 |        0.784979 |
    | 11.01. |           0.0 |         5.0 |   0.003114 |                   0.0 |               0.084 |             0.084 | 0.094737 |              0.784979 |             0.2 |        0.094737 |      0.034284 |            0.042796 |            0.0 | 0.034284 |    0.012456 |      0.042796 | 0.094737 | 0.034284 |         0.81852 |
    | 12.01. |           0.0 |         5.0 |   0.001877 |                   0.0 |              0.0968 |          0.096767 | 0.084211 |               0.81852 |             0.2 |        0.084211 |      0.019723 |            0.024987 |            0.0 | 0.019723 |    0.007509 |      0.024987 | 0.084211 | 0.019723 |        0.840207 |
    | 13.01. |           0.0 |         5.0 |   0.000812 |                   0.0 |             0.09936 |           0.09629 | 0.073684 |              0.840207 |             0.2 |        0.073684 |      0.011381 |            0.015318 |            0.0 | 0.011381 |    0.003249 |      0.015318 | 0.073684 | 0.011381 |         0.72592 |
    | 14.01. |           0.0 |         5.0 |   0.000133 |                   0.0 |            0.099872 |          0.079215 | 0.063158 |               0.72592 |             0.2 |        0.063158 |      0.006741 |            0.008625 |            0.0 | 0.006741 |    0.000534 |      0.008625 | 0.063158 | 0.006741 |        0.575373 |
    | 15.01. |           0.0 |         5.0 |  -0.000084 |                   0.0 |            0.099974 |          0.052067 | 0.052632 |              0.575373 |             0.2 |        0.052632 |      0.004844 |            0.005803 |            0.0 | 0.004844 |   -0.000337 |      0.005803 | 0.052632 | 0.004844 |        0.386003 |
    | 16.01. |           0.0 |         5.0 |  -0.000067 |                   0.0 |            0.099995 |          0.034075 | 0.042105 |              0.386003 |             0.2 |        0.042105 |      0.003618 |            0.003613 |            0.0 | 0.003618 |   -0.000268 |      0.003613 | 0.042105 | 0.003618 |        0.198088 |
    | 17.01. |           0.0 |         5.0 |  -0.000256 |                   0.0 |            0.099999 |          0.035719 | 0.031579 |              0.198088 |             0.2 |        0.031579 |      0.002733 |            0.001868 |            0.0 | 0.002733 |   -0.001023 |      0.001868 | 0.031579 | 0.002733 |        0.113577 |
    | 18.01. |           0.0 |         5.0 |  -0.000281 |                   0.0 |                 0.1 |          0.019524 | 0.021053 |              0.113577 |             0.2 |        0.021053 |      0.001686 |            0.000985 |            0.0 | 0.001686 |   -0.001122 |      0.000985 | 0.021053 | 0.001686 |         0.05798 |
    | 19.01. |           0.0 |         5.0 |  -0.000394 |                   0.0 |                 0.1 |           0.01451 | 0.010526 |               0.05798 |             0.2 |        0.010526 |      0.000808 |            0.000481 |            0.0 | 0.000808 |   -0.001578 |      0.000481 | 0.010526 | 0.000808 |        0.026921 |
    | 20.01. |           0.0 |         5.0 |  -0.000592 |                   0.0 |                 0.1 |          0.008923 |      0.0 |              0.026921 |             0.2 |             0.0 |           0.0 |             0.00021 |            0.0 |      0.0 |   -0.002367 |       0.00021 |      0.0 |      0.0 |             0.0 |

.. _dam_v003_flood_retention:

flood retention
_______________

This example repeats the :ref:`dam_v001_flood_retention` example of application model
|dam_v001| and the :ref:`dam_v002_flood_retention` example of application model
|dam_v002|.  We use the same parameter and input time series configuration:

>>> neardischargeminimumthreshold(0.0)
>>> neardischargeminimumtolerance(0.0)
>>> waterlevelminimumthreshold(0.0)
>>> waterlevelminimumtolerance(0.0)
>>> waterlevelminimumremotethreshold(0.0)
>>> waterlevelminimumremotetolerance(0.0)
>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 2.5]))
>>> inputs.precipitation.series = [0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inflow.sequences.sim.series = [0.0, 0.0, 5.0, 9.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inputs.evaporation.series = 0.0
>>> required_supply.sequences.sim.series = 0.0
>>> test.inits.loggedrequiredremoterelease = 0.0

The following results demonstrate that |dam_v003| calculates the same outflow values as
|dam_v001| and |dam_v002| if there is no relevant remote demand:

.. integration-test::

    >>> test("dam_v003_flood_retention")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply | inflow |  outflow | required_supply |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |            0.0 |      0.0 |         0.0 |           0.0 |    0.0 |      0.0 |             0.0 |
    | 02.01. |          50.0 |         0.0 |   0.021027 |                   1.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.026514 | 0.026514 |    0.084109 |           0.0 |    0.0 | 0.026514 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.125058 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.183744 | 0.183744 |    0.500234 |           0.0 |    5.0 | 0.183744 |             0.0 |
    | 04.01. |           0.0 |         0.0 |    0.30773 |                   0.0 |                 0.0 |               0.0 |    9.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.542983 | 0.542983 |     1.23092 |           0.0 |    9.0 | 0.542983 |             0.0 |
    | 05.01. |           0.0 |         0.0 |   0.459772 |                   0.0 |                 0.0 |               0.0 |    8.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.961039 | 0.961039 |    1.839086 |           0.0 |    8.0 | 0.961039 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.540739 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.251523 | 1.251523 |    2.162955 |           0.0 |    5.0 | 1.251523 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.575395 |                   0.0 |                 0.0 |               0.0 |    3.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.395546 | 1.395546 |    2.301579 |           0.0 |    3.0 | 1.395546 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.587202 |                   0.0 |                 0.0 |               0.0 |    2.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.453375 | 1.453375 |    2.348808 |           0.0 |    2.0 | 1.453375 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.577361 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.455596 | 1.455596 |    2.309444 |           0.0 |    1.0 | 1.455596 |             0.0 |
    | 10.01. |           0.0 |         0.0 |    0.54701 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.405132 | 1.405132 |    2.188041 |           0.0 |    0.0 | 1.405132 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.518255 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.331267 | 1.331267 |    2.073019 |           0.0 |    0.0 | 1.331267 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.491011 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.261285 | 1.261285 |    1.964044 |           0.0 |    0.0 | 1.261285 |             0.0 |
    | 13.01. |           0.0 |         0.0 |     0.4652 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.194981 | 1.194981 |    1.860798 |           0.0 |    0.0 | 1.194981 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.440745 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.132163 | 1.132163 |    1.762979 |           0.0 |    0.0 | 1.132163 |             0.0 |
    | 15.01. |           0.0 |         0.0 |   0.417576 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.072647 | 1.072647 |    1.670302 |           0.0 |    0.0 | 1.072647 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.395624 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.01626 |  1.01626 |    1.582498 |           0.0 |    0.0 |  1.01626 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.374827 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.962837 | 0.962837 |    1.499308 |           0.0 |    0.0 | 0.962837 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.355123 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.912222 | 0.912222 |    1.420492 |           0.0 |    0.0 | 0.912222 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.336455 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.864268 | 0.864268 |     1.34582 |           0.0 |    0.0 | 0.864268 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.318768 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.818835 | 0.818835 |    1.275072 |           0.0 |    0.0 | 0.818835 |             0.0 |
"""

# import...
# ...from standard library
from hydpy.core import modeltools

# ...from HydPy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.exe.modelimports import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(modeltools.ELSModel):
    """Version 3 of HydPy-Dam."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        dam_model.Calc_AdjustedEvaporation_V1,
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_RequiredRemoteRelease_V2,
        dam_model.Calc_RequiredRelease_V2,
        dam_model.Calc_TargetedRelease_V1,
    )
    RECEIVER_METHODS = (dam_model.Pic_LoggedRequiredRemoteRelease_V2,)
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_ActualRelease_V1,
        dam_model.Calc_ActualRemoteRelease_V1,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_Outflow_V1,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V2,)
    OUTLET_METHODS = (
        dam_model.Calc_WaterLevel_V1,
        dam_model.Pass_Outflow_V1,
        dam_model.Pass_ActualRemoteRelease_V1,
    )
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
