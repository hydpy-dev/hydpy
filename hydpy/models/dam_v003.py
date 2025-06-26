# pylint: disable=line-too-long, unused-wildcard-import
"""
|dam_v003| is quite similar to |dam_v002|.  Both application models provide the same
flood retention functionalities.  Also, both try to meet the water demand at a remote
location.  The difference is that |dam_v002| expects this demand to occur in the
channel downstream (usually to increase low discharge values).  Instead, |dam_v003|
supplies water to a different location (such as a drinking water treatment plant).
Hence, |dam_v002| releases its water via a single output path while |dam_v003| divides
it into two separate paths.

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
`outflow` node of the documentation on |dam_v001| and |dam_v002| and passes the
received outflow into the channel immediately downstream of the dam.  Node
`actual_supply` is new and serves to supply a different location with water.  Node
`required_supply` is equivalent to node `demand` of the documentation on |dam_v002|.
It delivers the same information but from a different location:

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
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.017174 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |             0.2 |             0.2 |      0.199917 |            0.004998 |            0.0 | 0.199917 |    0.068695 |      0.004998 |    1.0 | 0.199917 |        0.008588 |
    | 02.01. |   0.034268 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.008588 |             0.2 |             0.2 |           0.2 |            0.008588 |            0.0 |      0.2 |    0.137073 |      0.008588 |    1.0 |      0.2 |        0.010053 |
    | 03.01. |   0.051331 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.010053 |             0.2 |             0.2 |           0.2 |            0.010053 |            0.0 |      0.2 |    0.205325 |      0.010053 |    1.0 |      0.2 |        0.013858 |
    | 04.01. |   0.068312 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.013858 |             0.2 |             0.2 |           0.2 |            0.013858 |            0.0 |      0.2 |    0.273247 |      0.013858 |    1.0 |      0.2 |        0.027322 |
    | 05.01. |   0.085002 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.027322 |             0.2 |             0.2 |           0.2 |            0.027322 |            0.0 |      0.2 |    0.340007 |      0.027322 |    1.0 |      0.2 |        0.064075 |
    | 06.01. |   0.100898 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.064075 |             0.2 |             0.2 |           0.2 |            0.064075 |            0.0 |      0.2 |    0.403591 |      0.064075 |    1.0 |      0.2 |        0.235523 |
    | 07.01. |    0.11309 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.235523 |             0.2 |             0.2 |           0.2 |            0.235523 |            0.0 |      0.2 |    0.452362 |      0.235523 |    1.0 |      0.2 |        0.470414 |
    | 08.01. |   0.120209 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.470414 |             0.2 |             0.2 |           0.2 |            0.470414 |            0.0 |      0.2 |    0.480838 |      0.470414 |    1.0 |      0.2 |        0.735001 |
    | 09.01. |   0.121613 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.735001 |             0.2 |             0.2 |           0.2 |            0.735001 |            0.0 |      0.2 |    0.486454 |      0.735001 |    1.0 |      0.2 |        0.891263 |
    | 10.01. |   0.119642 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.891263 |             0.2 |             0.2 |           0.2 |            0.891263 |            0.0 |      0.2 |    0.478569 |      0.891263 |    1.0 |      0.2 |        0.696325 |
    | 11.01. |   0.121882 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.696325 |             0.2 |             0.2 |           0.2 |            0.696325 |            0.0 |      0.2 |    0.487526 |      0.696325 |    1.0 |      0.2 |        0.349797 |
    | 12.01. |   0.131606 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.349797 |             0.2 |             0.2 |           0.2 |            0.349797 |            0.0 |      0.2 |    0.526424 |      0.349797 |    1.0 |      0.2 |        0.105231 |
    | 13.01. |   0.146613 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.105231 |             0.2 |             0.2 |           0.2 |            0.105231 |            0.0 |      0.2 |    0.586452 |      0.105231 |    1.0 |      0.2 |        0.111928 |
    | 14.01. |   0.161475 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.111928 |             0.2 |             0.2 |           0.2 |            0.111928 |            0.0 |      0.2 |    0.645901 |      0.111928 |    1.0 |      0.2 |        0.240436 |
    | 15.01. |   0.173562 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.240436 |             0.2 |             0.2 |           0.2 |            0.240436 |            0.0 |      0.2 |    0.694247 |      0.240436 |    1.0 |      0.2 |        0.229369 |
    | 16.01. |   0.185887 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.229369 |             0.2 |             0.2 |           0.2 |            0.229369 |            0.0 |      0.2 |     0.74355 |      0.229369 |    1.0 |      0.2 |        0.058622 |
    | 17.01. |   0.201901 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.058622 |             0.2 |             0.2 |           0.2 |            0.058622 |            0.0 |      0.2 |    0.807605 |      0.058622 |    1.0 |      0.2 |        0.016958 |
    | 18.01. |   0.218815 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.016958 |             0.2 |             0.2 |           0.2 |            0.016958 |            0.0 |      0.2 |     0.87526 |      0.016958 |    1.0 |      0.2 |        0.008447 |
    | 19.01. |   0.235913 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.008447 |             0.2 |             0.2 |           0.2 |            0.008447 |            0.0 |      0.2 |     0.94365 |      0.008447 |    1.0 |      0.2 |        0.004155 |
    | 20.01. |   0.253103 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.004155 |             0.2 |             0.2 |           0.2 |            0.004155 |            0.0 |      0.2 |    1.012411 |      0.004155 |    1.0 |      0.2 |             0.0 |

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
only concerns the release into the channel downstream:

.. integration-test::

    >>> test("dam_v003_restriction_enabled")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.017174 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |             0.2 |             0.2 |      0.199917 |            0.004998 |            0.0 | 0.199917 |    0.068695 |      0.004998 |    1.0 | 0.199917 |        0.008746 |
    | 02.01. |   0.034265 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.008746 |             0.2 |             0.2 |           0.2 |            0.008746 |            0.0 |      0.2 |     0.13706 |      0.008746 |    1.0 |      0.2 |        0.010632 |
    | 03.01. |   0.051315 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.010632 |             0.2 |             0.2 |           0.2 |            0.010632 |            0.0 |      0.2 |    0.205261 |      0.010632 |    1.0 |      0.2 |        0.015099 |
    | 04.01. |   0.068269 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.015099 |             0.2 |             0.2 |           0.2 |            0.015099 |            0.0 |      0.2 |    0.273077 |      0.015099 |    1.0 |      0.2 |         0.03006 |
    | 05.01. |     0.0849 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |               0.03006 |             0.2 |             0.2 |           0.2 |             0.03006 |            0.0 |      0.2 |    0.339599 |       0.03006 |    1.0 |      0.2 |        0.068641 |
    | 06.01. |   0.100697 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.068641 |             0.2 |             0.2 |           0.2 |            0.068641 |            0.0 |      0.2 |    0.402789 |      0.068641 |    1.0 |      0.2 |        0.242578 |
    | 07.01. |   0.112738 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.242578 |             0.2 |             0.2 |           0.2 |            0.242578 |            0.0 |      0.2 |     0.45095 |      0.242578 |    1.0 |      0.2 |        0.474285 |
    | 08.01. |   0.119773 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.474285 |             0.2 |             0.2 |           0.2 |            0.474285 |            0.0 |      0.2 |    0.479092 |      0.474285 |    1.0 |      0.2 |        0.784512 |
    | 09.01. |   0.120108 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              0.784512 |             0.2 |             0.2 |           0.2 |            0.784512 |            0.0 |      0.2 |     0.48043 |      0.784512 |    1.0 |      0.2 |         0.95036 |
    | 10.01. |    0.11686 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |               0.95036 |             0.2 |             0.2 |           0.2 |             0.95036 |            0.0 |      0.2 |    0.467439 |       0.95036 |    1.0 |      0.2 |            0.35 |
    | 11.01. |     0.1093 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  0.35 |             0.2 |             0.1 |           0.1 |                0.35 |            0.0 |      0.1 |    0.437199 |          0.35 |    0.1 |      0.1 |        0.034564 |
    | 12.01. |   0.108553 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.034564 |             0.2 |             0.1 |           0.1 |            0.034564 |            0.0 |      0.1 |    0.434213 |      0.034564 |    0.1 |      0.1 |        0.299482 |
    | 13.01. |   0.102084 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.299482 |             0.2 |             0.1 |           0.1 |            0.299482 |            0.0 |      0.1 |    0.408337 |      0.299482 |    0.1 |      0.1 |        0.585979 |
    | 14.01. |   0.089427 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.585979 |             0.2 |             0.1 |           0.1 |            0.585979 |            0.0 |      0.1 |    0.357709 |      0.585979 |    0.1 |      0.1 |        0.557422 |
    | 15.01. |   0.077387 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.557422 |             0.2 |             0.1 |           0.1 |            0.557422 |            0.0 |      0.1 |    0.309547 |      0.557422 |    0.1 |      0.1 |        0.229369 |
    | 16.01. |   0.072432 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.229369 |             0.2 |             0.1 |           0.1 |            0.229369 |            0.0 |      0.1 |     0.28973 |      0.229369 |    0.1 |      0.1 |        0.142578 |
    | 17.01. |   0.069353 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.142578 |             0.2 |             0.1 |           0.1 |            0.142578 |            0.0 |      0.1 |    0.277411 |      0.142578 |    0.1 |      0.1 |        0.068641 |
    | 18.01. |    0.06787 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.068641 |             0.2 |             0.1 |           0.1 |            0.068641 |            0.0 |      0.1 |    0.271481 |      0.068641 |    0.1 |      0.1 |        0.029844 |
    | 19.01. |   0.067226 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.029844 |             0.2 |             0.1 |           0.1 |            0.029844 |            0.0 |      0.1 |    0.268902 |      0.029844 |    0.1 |      0.1 |        0.012348 |
    | 20.01. |   0.066959 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |              0.012348 |             0.2 |             0.1 |           0.1 |            0.012348 |            0.0 |      0.1 |    0.267835 |      0.012348 |    0.1 |      0.1 |             0.0 |

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

Additionally, we illustrate the control parameters unknown to |dam_v001| and
|dam_v002|, |WaterLevelMinimumRemoteThreshold|, and |WaterLevelMinimumRemoteTolerance|.
Separate water level-related threshold values for the near demand
(|WaterLevelMinimumThreshold|) and the remote demand
(|WaterLevelMinimumRemoteThreshold|) and their smoothing parameters allow for a
distinct configuration of both output paths in situations when the available storage is
limited.  Here, we set |WaterLevelMinimumRemoteThreshold| to a higher value than
|WaterLevelMinimumThreshold|.  Hence, the release into the channel downstream has
priority over the supply to the remote location:

>>> waterlevelminimumremotetolerance(0.01)
>>> waterlevelminimumremotethreshold(0.01)

.. integration-test::

    >>> test("dam_v003_smooth_stage_minimum")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation |   inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply |   inflow |  outflow | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.003462 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |      0.2 |                 0.005 |             0.2 |             0.2 |      0.039605 |            0.000125 |            0.0 | 0.039605 |    0.013847 |      0.000125 |      0.2 | 0.039605 |         0.01232 |
    | 02.01. |   0.005651 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.189474 |               0.01232 |             0.2 |        0.189474 |       0.08713 |            0.000999 |            0.0 |  0.08713 |    0.022604 |      0.000999 | 0.189474 |  0.08713 |        0.029323 |
    | 03.01. |   0.006915 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.178947 |              0.029323 |             0.2 |        0.178947 |      0.115815 |            0.004617 |            0.0 | 0.115815 |    0.027659 |      0.004617 | 0.178947 | 0.115815 |        0.064084 |
    | 04.01. |    0.00756 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.168421 |              0.064084 |             0.2 |        0.168421 |      0.124349 |            0.014199 |            0.0 | 0.124349 |     0.03024 |      0.014199 | 0.168421 | 0.124349 |        0.120198 |
    | 05.01. |    0.00769 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.157895 |              0.120198 |             0.2 |        0.157895 |      0.121593 |            0.030276 |            0.0 | 0.121593 |    0.030761 |      0.030276 | 0.157895 | 0.121593 |        0.247367 |
    | 06.01. |   0.007221 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.147368 |              0.247367 |             0.2 |        0.147368 |      0.110974 |            0.058113 |            0.0 | 0.110974 |    0.028885 |      0.058113 | 0.147368 | 0.110974 |         0.45567 |
    | 07.01. |   0.006355 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.136842 |               0.45567 |             0.2 |        0.136842 |      0.094052 |            0.082892 |            0.0 | 0.094052 |     0.02542 |      0.082892 | 0.136842 | 0.094052 |        0.608464 |
    | 08.01. |   0.005656 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.126316 |              0.608464 |             0.2 |        0.126316 |      0.076665 |            0.082026 |            0.0 | 0.076665 |    0.022622 |      0.082026 | 0.126316 | 0.076665 |        0.537314 |
    | 09.01. |   0.005435 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.115789 |              0.537314 |             0.2 |        0.115789 |      0.064915 |            0.061095 |            0.0 | 0.064915 |    0.021739 |      0.061095 | 0.115789 | 0.064915 |        0.629775 |
    | 10.01. |   0.005122 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.105263 |              0.629775 |             0.2 |        0.105263 |      0.055735 |            0.064032 |            0.0 | 0.055735 |    0.020486 |      0.064032 | 0.105263 | 0.055735 |        0.744091 |
    | 11.01. |    0.00475 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.094737 |              0.744091 |             0.2 |        0.094737 |        0.0464 |            0.065527 |            0.0 |   0.0464 |    0.019001 |      0.065527 | 0.094737 |   0.0464 |         0.82219 |
    | 12.01. |   0.004406 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.084211 |               0.82219 |             0.2 |        0.084211 |      0.037828 |            0.062332 |            0.0 | 0.037828 |    0.017623 |      0.062332 | 0.084211 | 0.037828 |        0.841916 |
    | 13.01. |   0.004127 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.073684 |              0.841916 |             0.2 |        0.073684 |      0.030563 |             0.05601 |            0.0 | 0.030563 |    0.016509 |       0.05601 | 0.073684 | 0.030563 |        0.701812 |
    | 14.01. |   0.004021 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.063158 |              0.701812 |             0.2 |        0.063158 |      0.024926 |            0.043161 |            0.0 | 0.024926 |    0.016084 |      0.043161 | 0.063158 | 0.024926 |        0.533258 |
    | 15.01. |   0.004021 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.052632 |              0.533258 |             0.2 |        0.052632 |      0.020495 |            0.032121 |            0.0 | 0.020495 |    0.016085 |      0.032121 | 0.052632 | 0.020495 |        0.351863 |
    | 16.01. |   0.004106 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.042105 |              0.351863 |             0.2 |        0.042105 |      0.016599 |            0.021602 |            0.0 | 0.016599 |    0.016422 |      0.021602 | 0.042105 | 0.016599 |        0.185207 |
    | 17.01. |   0.004252 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.031579 |              0.185207 |             0.2 |        0.031579 |      0.012852 |            0.011952 |            0.0 | 0.012852 |    0.017008 |      0.011952 | 0.031579 | 0.012852 |        0.107697 |
    | 18.01. |   0.004357 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.021053 |              0.107697 |             0.2 |        0.021053 |      0.008861 |            0.007331 |            0.0 | 0.008861 |    0.017428 |      0.007331 | 0.021053 | 0.008861 |        0.055458 |
    | 19.01. |   0.004402 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.010526 |              0.055458 |             0.2 |        0.010526 |      0.004519 |            0.003898 |            0.0 | 0.004519 |     0.01761 |      0.003898 | 0.010526 | 0.004519 |        0.025948 |
    | 20.01. |   0.004363 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |      0.0 |              0.025948 |             0.2 |             0.0 |           0.0 |            0.001826 |            0.0 |      0.0 |    0.017452 |      0.001826 |      0.0 |      0.0 |             0.0 |

.. _dam_v003_evaporation:

evaporation
___________

This example corresponds to the :ref:`dam_v001_evaporation` example of application model
|dam_v001| and the :ref:`dam_v002_evaporation` example of application model |dam_v002|.
We add an |evap_ret_io| submodel and update the required remote release time series
accordingly:

>>> with model.add_pemodel_v1("evap_ret_io") as pemodel:
...     evapotranspirationfactor(1.0)
>>> pemodel.prepare_inputseries()
>>> pemodel.sequences.inputs.referenceevapotranspiration.series = 10 * [1.0] + 10 * [5.0]
>>> required_supply.sequences.sim.series = [
...     0.012321, 0.029352, 0.064305, 0.120897, 0.248435, 0.453671, 0.585089,
...     0.550583, 0.694398, 0.784979, 0.81852, 0.840207, 0.72592, 0.575373,
...     0.386003, 0.198088, 0.113577, 0.05798, 0.026921, 0.0]

Due to the remaining differences regarding remote demand, the following results differ
from those of |dam_v001| and |dam_v002|.  However, detailed comparisons show the same
patterns for adjusting potential evaporation and its conversion to actual evaporation
under water scarcity:

.. integration-test::

    >>> test("dam_v003_evaporation")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation |   inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply |   inflow |  outflow | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.003181 |           0.0 |                   0.0 |                  1.0 |               0.016 |          0.015347 |      0.2 |                 0.005 |             0.2 |             0.2 |      0.037276 |            0.000116 |            0.0 | 0.037276 |    0.012723 |      0.000116 |      0.2 | 0.037276 |        0.012321 |
    | 02.01. |   0.005144 |           0.0 |                   0.0 |                  1.0 |              0.0192 |            0.0192 | 0.189474 |              0.012321 |             0.2 |        0.189474 |      0.078569 |            0.000837 |            0.0 | 0.078569 |    0.020574 |      0.000837 | 0.189474 | 0.078569 |        0.029352 |
    | 03.01. |   0.006246 |           0.0 |                   0.0 |                  1.0 |             0.01984 |           0.01984 | 0.178947 |              0.029352 |             0.2 |        0.178947 |      0.104408 |            0.003653 |            0.0 | 0.104408 |    0.024985 |      0.003653 | 0.178947 | 0.104408 |        0.064305 |
    | 04.01. |   0.006783 |           0.0 |                   0.0 |                  1.0 |            0.019968 |          0.019968 | 0.168421 |              0.064305 |             0.2 |        0.168421 |      0.112714 |             0.01089 |            0.0 | 0.112714 |    0.027132 |       0.01089 | 0.168421 | 0.112714 |        0.120897 |
    | 05.01. |   0.006882 |           0.0 |                   0.0 |                  1.0 |            0.019994 |          0.019994 | 0.157895 |              0.120897 |             0.2 |        0.157895 |      0.110416 |            0.022906 |            0.0 | 0.110416 |    0.027527 |      0.022906 | 0.157895 | 0.110416 |        0.248435 |
    | 06.01. |   0.006503 |           0.0 |                   0.0 |                  1.0 |            0.019999 |          0.019999 | 0.147368 |              0.248435 |             0.2 |        0.147368 |       0.10065 |            0.044264 |            0.0 |  0.10065 |    0.026011 |      0.044264 | 0.147368 |  0.10065 |        0.453671 |
    | 07.01. |   0.005786 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 | 0.136842 |              0.453671 |             0.2 |        0.136842 |      0.085218 |            0.064794 |            0.0 | 0.085218 |    0.023146 |      0.064794 | 0.136842 | 0.085218 |        0.585089 |
    | 08.01. |   0.005189 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 | 0.126316 |              0.585089 |             0.2 |        0.126316 |      0.069588 |            0.064373 |            0.0 | 0.069588 |    0.020757 |      0.064373 | 0.126316 | 0.069588 |        0.550583 |
    | 09.01. |   0.004901 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 | 0.115789 |              0.550583 |             0.2 |        0.115789 |      0.058259 |            0.050888 |            0.0 | 0.058259 |    0.019603 |      0.050888 | 0.115789 | 0.058259 |        0.694398 |
    | 10.01. |   0.004496 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 | 0.105263 |              0.694398 |             0.2 |        0.105263 |      0.048686 |            0.055331 |            0.0 | 0.048686 |    0.017983 |      0.055331 | 0.105263 | 0.048686 |        0.784979 |
    | 11.01. |   0.003086 |           0.0 |                   0.0 |                  5.0 |               0.084 |             0.084 | 0.094737 |              0.784979 |             0.2 |        0.094737 |      0.033924 |            0.042097 |            0.0 | 0.033924 |    0.012342 |      0.042097 | 0.094737 | 0.033924 |         0.81852 |
    | 12.01. |   0.001849 |           0.0 |                   0.0 |                  5.0 |              0.0968 |          0.096796 | 0.084211 |               0.81852 |             0.2 |        0.084211 |       0.01987 |            0.024773 |            0.0 |  0.01987 |    0.007398 |      0.024773 | 0.084211 |  0.01987 |        0.840207 |
    | 13.01. |    0.00074 |           0.0 |                   0.0 |                  5.0 |             0.09936 |          0.098662 | 0.073684 |              0.840207 |             0.2 |        0.073684 |       0.01131 |            0.015082 |            0.0 |  0.01131 |    0.002959 |      0.015082 | 0.073684 |  0.01131 |         0.72592 |
    | 14.01. |   0.000083 |           0.0 |                   0.0 |                  5.0 |            0.099872 |          0.078473 | 0.063158 |               0.72592 |             0.2 |        0.063158 |      0.006629 |            0.008462 |            0.0 | 0.006629 |    0.000332 |      0.008462 | 0.063158 | 0.006629 |        0.575373 |
    | 15.01. |  -0.000055 |           0.0 |                   0.0 |                  5.0 |            0.099974 |          0.048539 | 0.052632 |              0.575373 |             0.2 |        0.052632 |      0.004782 |            0.005722 |            0.0 | 0.004782 |   -0.000222 |      0.005722 | 0.052632 | 0.004782 |        0.386003 |
    | 16.01. |  -0.000129 |           0.0 |                   0.0 |                  5.0 |            0.099995 |          0.038137 | 0.042105 |              0.386003 |             0.2 |        0.042105 |      0.003679 |            0.003679 |            0.0 | 0.003679 |   -0.000515 |      0.003679 | 0.042105 | 0.003679 |        0.198088 |
    | 17.01. |  -0.000204 |           0.0 |                   0.0 |                  5.0 |            0.099999 |          0.030567 | 0.031579 |              0.198088 |             0.2 |        0.031579 |      0.002676 |            0.001826 |            0.0 | 0.002676 |   -0.000816 |      0.001826 | 0.031579 | 0.002676 |        0.113577 |
    | 18.01. |  -0.000301 |           0.0 |                   0.0 |                  5.0 |                 0.1 |          0.022795 | 0.021053 |              0.113577 |             0.2 |        0.021053 |      0.001719 |            0.001006 |            0.0 | 0.001719 |   -0.001202 |      0.001006 | 0.021053 | 0.001719 |         0.05798 |
    | 19.01. |  -0.000428 |           0.0 |                   0.0 |                  5.0 |                 0.1 |          0.015126 | 0.010526 |               0.05798 |             0.2 |        0.010526 |       0.00082 |            0.000488 |            0.0 |  0.00082 |   -0.001713 |      0.000488 | 0.010526 |  0.00082 |        0.026921 |
    | 20.01. |  -0.000609 |           0.0 |                   0.0 |                  5.0 |                 0.1 |          0.008146 |      0.0 |              0.026921 |             0.2 |             0.0 |           0.0 |            0.000211 |            0.0 |      0.0 |   -0.002435 |      0.000211 |      0.0 |      0.0 |             0.0 |

>>> del model.pemodel

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
>>> with model.add_precipmodel_v2("meteo_precip_io") as precipmodel:
...     precipitationfactor(1.0)
>>> precipmodel.prepare_inputseries()
>>> precipmodel.sequences.inputs.precipitation.series = [
...     0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inflow.sequences.sim.series = [0.0, 0.0, 5.0, 9.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> required_supply.sequences.sim.series = 0.0
>>> test.inits.loggedrequiredremoterelease = 0.0

The following results demonstrate that |dam_v003| calculates the same outflow values as
|dam_v001| and |dam_v002| if there is no relevant remote demand:

.. integration-test::

    >>> test("dam_v003_flood_retention")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_supply | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |            0.0 |      0.0 |         0.0 |           0.0 |    0.0 |      0.0 |             0.0 |
    | 02.01. |   0.021027 |          50.0 |                   1.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.026521 | 0.026521 |    0.084109 |           0.0 |    0.0 | 0.026521 |             0.0 |
    | 03.01. |   0.125058 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.183777 | 0.183777 |     0.50023 |           0.0 |    5.0 | 0.183777 |             0.0 |
    | 04.01. |   0.307728 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    9.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.543038 | 0.543038 |    1.230912 |           0.0 |    9.0 | 0.543038 |             0.0 |
    | 05.01. |   0.459769 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    8.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.961082 | 0.961082 |    1.839074 |           0.0 |    8.0 | 0.961082 |             0.0 |
    | 06.01. |   0.540735 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.251541 | 1.251541 |    2.162941 |           0.0 |    5.0 | 1.251541 |             0.0 |
    | 07.01. |   0.575391 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.395548 | 1.395548 |    2.301566 |           0.0 |    3.0 | 1.395548 |             0.0 |
    | 08.01. |   0.587199 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.453371 | 1.453371 |    2.348795 |           0.0 |    2.0 | 1.453371 |             0.0 |
    | 09.01. |   0.577358 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.455585 | 1.455585 |    2.309432 |           0.0 |    1.0 | 1.455585 |             0.0 |
    | 10.01. |   0.547008 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.405115 | 1.405115 |     2.18803 |           0.0 |    0.0 | 1.405115 |             0.0 |
    | 11.01. |   0.518253 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.331251 | 1.331251 |     2.07301 |           0.0 |    0.0 | 1.331251 |             0.0 |
    | 12.01. |   0.491009 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.26127 |  1.26127 |    1.964036 |           0.0 |    0.0 |  1.26127 |             0.0 |
    | 13.01. |   0.465198 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.194968 | 1.194968 |    1.860791 |           0.0 |    0.0 | 1.194968 |             0.0 |
    | 14.01. |   0.440743 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.132151 | 1.132151 |    1.762973 |           0.0 |    0.0 | 1.132151 |             0.0 |
    | 15.01. |   0.417574 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.072636 | 1.072636 |    1.670297 |           0.0 |    0.0 | 1.072636 |             0.0 |
    | 16.01. |   0.395623 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.01625 |  1.01625 |    1.582493 |           0.0 |    0.0 |  1.01625 |             0.0 |
    | 17.01. |   0.374826 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.962828 | 0.962828 |    1.499305 |           0.0 |    0.0 | 0.962828 |             0.0 |
    | 18.01. |   0.355122 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.912214 | 0.912214 |     1.42049 |           0.0 |    0.0 | 0.912214 |             0.0 |
    | 19.01. |   0.336454 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.864261 | 0.864261 |    1.345818 |           0.0 |    0.0 | 0.864261 |             0.0 |
    | 20.01. |   0.318768 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.818829 | 0.818829 |    1.275071 |           0.0 |    0.0 | 0.818829 |             0.0 |
"""

# import...
# ...from HydPy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces


# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(dam_model.Main_PrecipModel_V2, dam_model.Main_PEModel_V1):
    """|dam_v003.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Dam-V3", description="dam model, version 3")
    __HYDPY_ROOTMODEL__ = True

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
        dam_model.Pick_Inflow_V1,
        dam_model.Calc_RequiredRemoteRelease_V2,
        dam_model.Calc_RequiredRelease_V2,
        dam_model.Calc_TargetedRelease_V1,
    )
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = (dam_model.Pick_LoggedRequiredRemoteRelease_V2,)
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pick_Inflow_V1,
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
    SUBMODELINTERFACES = (precipinterfaces.PrecipModel_V2, petinterfaces.PETModel_V1)
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)


tester = Tester()
cythonizer = Cythonizer()
