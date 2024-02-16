# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Version 5 application model of HydPy-Dam.

Application model |dam_v005| extends |dam_v001| with two features enabling
collaboration with other dam models for better drought and flood prevention.

Like |dam_v001|, |dam_v005| tries to increase the discharge at a remote location in the
channel downstream during low flow conditions and sometimes fails due to its limited
storage content.  The first additional feature of |dam_v005| is that it passes the
information on its anticipated failure to another remote location.  This information
enables other models to jump in when necessary.

The second additional feature of |dam_v005| is that it receives input from two
additional inlet nodes, one passing "supply discharge" and the other one "relief
discharge".  We understand "supply discharge" as water delivered from a remote location
to increase the storage content of |dam_v005| when necessary (during droughts).  In
contrast, relief discharge serves to relieve the other location (possibly another dam)
during floods.  |dam_v005| calculates both the desirable supply discharge and the
acceptable relief discharge and passes that information to a single or two separate
remote locations.

The following explanations focus on these differences.  For further information on
using |dam_v005|, please read the documentation on model |dam_v001|.  Besides that, see
the documentation on |dam_v002| and |dam_v004|, which are possible counterparts for
|dam_v005|.

Integration tests
=================

.. how_to_understand_integration_tests::

The following integration tests build on some of the examples demonstrating the
functionality of model |dam_v001|.  To achieve comparability, we define identical
parameter values, initial conditions, and input time series.  The following
explanations focus on the differences between applications models |dam_v005| and
|dam_v001|.

The following time-related setup is identical to the one of |dam_v001|:

>>> from hydpy import pub
>>> pub.timegrids = "01.01.2000", "21.01.2000",  "1d"

Due to the high complexity of |dam_v005| and our test setting, which includes two
instances of another model type  (|arma_v1|), we need to define lots of |Node| objects:

>>> from hydpy import Node
>>> inflow = Node("inflow", variable="Q")
>>> outflow = Node("outflow", variable="Q")
>>> natural = Node("natural", variable="Q")
>>> remote = Node("remote", variable="Q")
>>> actual_supply = Node("actual_supply", variable="S")
>>> required_supply = Node("required_supply", variable="S")
>>> allowed_relief = Node("allowed_relief", variable="R")
>>> actual_relief = Node("actual_relief", variable="R")
>>> demand = Node("demand", variable="D")
>>> from hydpy import Element
>>> dam = Element("dam",
...               inlets=(inflow, actual_supply, actual_relief),
...               outlets=outflow,
...               receivers=remote,
...               senders=(demand, required_supply, allowed_relief))
>>> stream1 = Element("stream1", inlets=outflow, outlets=remote)
>>> stream2 = Element("stream2", inlets=natural, outlets=remote)

The nodes `inflow` and `outflow` handle the "normal" discharge into and out of the dam.
Node `outflow` passes its values to the routing element `stream1`.  The second routing
element, `stream2`, represents a natural tributary and receives the "natural" discharge
of the subcatchment downstream of the dam provided by the `natural` node.  Both routing
elements give their outflow to node `remote`, representing the cross-section downstream
where discharge should not undercut a certain threshold.  So far, the setting is
identical to the one of the documentation on |dam_v001|.

|dam_v005| needs to connect to two additional inlet nodes and three sender nodes.  The
input nodes `actual_supply` and `actual_relief` handle the actual supply and relief
discharge from remote locations.  The sender nodes `required_supply` and
`allowed_relief` inform other models of the currently required supply and the allowed
relief.  The sender node `demand` tells other models about the estimated demand for
water at the cross-section downstream that it cannot currently release itself.


To enable |dam_v005| to connect the different involved sequences and nodes correctly,
we need to give suitable |Node.variable| values to the |Node| instances.  We use the
string literal "Q" for the inflow and the outflow node, "S" for both supply nodes, "R"
for both relief nodes, and "D" for node `demand`.  See the documentation on method
|Model.connect| for alternatives and more detailed explanations.

As mentioned above, |dam_v002| and |dam_v004| are good counterparts for |dam_v005|.
Including them in the following examples would lead to a better agreement with typical
use cases of |dam_v005|.  However, we do not want to further bloat up the already
scenario setting.  Hence, we prefer to apply a predefined discharge time series instead
of dynamically calculating the remote location discharges.

We configure both |arma_v1| models, the |IntegrationTest| object, and the initial
conditions precisely as in the |dam_v001| examples:

>>> from hydpy import prepare_model
>>> stream2.model = prepare_model("arma_v1")
>>> stream2.model.parameters.control.responses(((), (1.0,)))
>>> stream2.model.parameters.update()

>>> stream1.model = prepare_model("arma_v1")
>>> stream1.model.parameters.control.responses(((), (0.2, 0.4, 0.3, 0.1)))
>>> stream1.model.parameters.update()

>>> from hydpy.models.dam_v005 import *
>>> parameterstep("1d")
>>> dam.model = model

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(dam)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume

>>> test.inits=((states.watervolume, 0.0),
...             (logs.loggedadjustedevaporation, 0.0),
...             (logs.loggedtotalremotedischarge, 1.9),
...             (logs.loggedoutflow, 0.0),
...             (stream1.model.sequences.logs.login, 0.0))

The following control parameters are common to both models.  We apply the same values:

>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 0.25]))
>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0], ys=[0.0]))
>>> catchmentarea(86.4)
>>> nmblogentries(1)
>>> remotedischargeminimum(1.4)
>>> remotedischargesafety(0.5)
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

|dam_v005| implements six additional control parameters, three for calculating the
required supply (|HighestRemoteSupply|, |WaterLevelSupplyThreshold|, and
|WaterLevelSupplyTolerance|) and three for calculating the allowed relief
(|HighestRemoteRelief|, |WaterLevelReliefThreshold|, and |WaterLevelReliefTolerance|):

>>> highestremotesupply(1.0)
>>> waterlevelsupplythreshold(0.2)
>>> waterlevelsupplytolerance(0.05)
>>> highestremoterelief(5.0)
>>> waterlevelreliefthreshold(0.5)
>>> waterlevelrelieftolerance(0.05)

We define identical time series for the subcatchment's discharge time series:

>>> natural.sequences.sim.series = [1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 1.0,
...                                 1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]

In the initial examples on |dam_v001|, the model receives a constant inflow of 1.0 m³/s
from its single inlet node.  To work with the same input sum and prove that all node
connections work correctly, we set the "normal" inflow, the actual supply, and the
actual relief discharge to a constant value of 1/3 m³/s:

>>> inflow.sequences.sim.series = 1.0/3.0
>>> actual_supply.sequences.sim.series = 1.0/3.0
>>> actual_relief.sequences.sim.series = 1.0/3.0

.. _dam_v005_smooth_near_minimum:

smooth near minimum
___________________

This example extends the :ref:`dam_v001_smooth_near_minimum` example of application
model |dam_v001|.

All results achieved for the water level and the outflow agree exactly, confirming
that |dam_v005| captures the relevant functionalities of |dam_v001| correctly.  From
the results specific to |dam_v005|, inspecting those of sequence |RequiredRemoteSupply|
is most insightful.  At the beginning of the simulation period, they reflect the value
of parameter |HighestRemoteSupply| (1.0 m³/s).  When the water level reaches the value
of parameter |WaterLevelSupplyThreshold| (0.2 m, which corresponds to a water volume of
0.8 million m³), the required remote release decreases and finally reaches 0.0 m³/s.
This transition happens over a relatively long period due to the large value of the
smoothing parameter |WaterLevelSupplyTolerance| (0.05 m):

.. integration-test::

    >>> test("dam_v005_smooth_near_minimum")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | demand |   inflow | natural |  outflow |   remote | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.017055 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.842088 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |        0.210526 |        0.210526 |      0.210438 |                  0.0 |            0.0 | 0.210438 |    0.068218 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.8 | 0.210438 | 1.842088 |             1.0 |
    | 02.01. |   0.034099 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.826356 |               1.631649 |          0.0 |     -0.442088 |              0.008454 |                 5.0 |                  1.0 |        0.210905 |        0.210905 |      0.210905 |                  0.0 |            0.0 | 0.210905 |    0.136396 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.7 | 0.210905 | 1.826356 |             1.0 |
    | 03.01. |    0.05114 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.789703 |               1.615451 |          0.0 |     -0.426356 |              0.009744 |                 5.0 |             0.999999 |         0.21105 |         0.21105 |       0.21105 |                  0.0 |            0.0 |  0.21105 |    0.204561 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.6 |  0.21105 | 1.789703 |        0.999999 |
    | 04.01. |   0.068172 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.711032 |               1.578654 |          0.0 |     -0.389703 |              0.013541 |                 5.0 |             0.999995 |        0.211486 |        0.211486 |      0.211486 |                  0.0 |            0.0 | 0.211486 |    0.272689 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.5 | 0.211486 | 1.711032 |        0.999995 |
    | 05.01. |   0.085167 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.611636 |               1.499546 |          0.0 |     -0.311032 |              0.027123 |                 5.0 |             0.999974 |        0.213183 |        0.213183 |      0.213183 |                  0.0 |            0.0 | 0.213183 |     0.34067 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.4 | 0.213183 | 1.611636 |        0.999974 |
    | 06.01. |   0.102036 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.513633 |               1.398453 |     0.001547 |     -0.211636 |              0.064097 |                 5.0 |             0.999877 |        0.219047 |        0.219047 |      0.219047 |                  0.0 |            0.0 | 0.219047 |    0.408144 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.3 | 0.219047 | 1.513633 |        0.999877 |
    | 07.01. |   0.117514 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.429412 |               1.294586 |     0.105414 |     -0.113633 |              0.235573 |                 5.0 |              0.99949 |        0.283449 |        0.283449 |      0.283449 |                  0.0 |            0.0 | 0.283449 |    0.470054 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.2 | 0.283449 | 1.429412 |         0.99949 |
    | 08.01. |   0.128848 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.395462 |               1.145963 |     0.254037 |     -0.029412 |              0.470453 |                 5.0 |             0.998556 |        0.475248 |        0.475248 |      0.475248 |                  0.0 |            0.0 | 0.475248 |    0.515393 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.1 | 0.475248 | 1.395462 |        0.998556 |
    | 09.01. |   0.134566 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.444094 |               0.920213 |     0.479787 |      0.004538 |              0.734999 |                 5.0 |             0.997561 |        0.735279 |        0.735279 |      0.735279 |                  0.0 |            0.0 | 0.735279 |    0.538265 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.735279 | 1.444094 |        0.997561 |
    | 10.01. |   0.136915 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.643284 |               0.708815 |     0.691185 |     -0.044094 |              0.891212 |                 5.0 |             0.996975 |        0.891263 |        0.891263 |      0.891263 |                  0.0 |            0.0 | 0.891263 |     0.54766 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.891263 | 1.643284 |        0.996975 |
    | 11.01. |   0.143466 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.763953 |                0.75202 |      0.64798 |     -0.243284 |              0.696269 |                 5.0 |              0.99449 |        0.696694 |        0.696694 |      0.696694 |                  0.0 |            0.0 | 0.696694 |    0.573865 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.696694 | 1.763953 |         0.99449 |
    | 12.01. |   0.157152 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.692862 |               1.067259 |     0.332741 |     -0.363953 |              0.349774 |                 5.0 |             0.980882 |        0.366387 |        0.366387 |      0.366387 |                  0.0 |            0.0 | 0.366387 |    0.628609 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.366387 | 1.692862 |        0.980882 |
    | 13.01. |   0.173822 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.590339 |               1.326474 |     0.073526 |     -0.292862 |              0.105265 |                 5.0 |             0.917269 |         0.22825 |         0.22825 |       0.22825 |                  0.0 |            0.0 |  0.22825 |    0.695289 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.1 |  0.22825 | 1.590339 |        0.917269 |
    | 14.01. |   0.190453 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.516899 |                1.36209 |      0.03791 |     -0.190339 |               0.11198 |                 5.0 |             0.706288 |        0.230069 |        0.230069 |      0.230069 |                  0.0 |            0.0 | 0.230069 |    0.761811 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.2 | 0.230069 | 1.516899 |        0.706288 |
    | 15.01. |   0.205867 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.554419 |                1.28683 |      0.11317 |     -0.116899 |               0.24046 |                 5.0 |             0.368383 |        0.286388 |        0.286388 |      0.286388 |                  0.0 |            0.0 | 0.286388 |    0.823467 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.3 | 0.286388 | 1.554419 |        0.368383 |
    | 16.01. |   0.221423 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.662362 |                1.26803 |      0.13197 |     -0.154419 |              0.229367 |                 5.0 |             0.122517 |        0.279806 |        0.279806 |      0.279806 |                  0.0 |            0.0 | 0.279806 |    0.885691 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.4 | 0.279806 | 1.662362 |        0.122517 |
    | 17.01. |   0.238313 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.764455 |               1.382556 |     0.017444 |     -0.262362 |              0.058606 |                 5.0 |             0.028719 |        0.218048 |        0.218048 |      0.218048 |                  0.0 |            0.0 | 0.218048 |    0.953252 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.5 | 0.218048 | 1.764455 |        0.028719 |
    | 18.01. |   0.255336 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.842178 |               1.546408 |          0.0 |     -0.364455 |              0.016957 |                 5.0 |             0.006148 |        0.211892 |        0.211892 |      0.211892 |                  0.0 |            0.0 | 0.211892 |    1.021345 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.6 | 0.211892 | 1.842178 |        0.006148 |
    | 19.01. |   0.272381 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.920333 |               1.630286 |          0.0 |     -0.442178 |              0.008447 |                 5.0 |              0.00129 |        0.210904 |        0.210904 |      0.210904 |                  0.0 |            0.0 | 0.210904 |    1.089522 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.7 | 0.210904 | 1.920333 |         0.00129 |
    | 20.01. |   0.289435 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             2.011821 |               1.709429 |          0.0 |     -0.520333 |              0.004155 |                 5.0 |             0.000269 |        0.210435 |        0.210435 |      0.210435 |                  0.0 |            0.0 | 0.210435 |    1.157741 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.8 | 0.210435 | 2.011821 |        0.000269 |

.. _dam_v005_restriction_enabled:

restriction enabled
___________________

This example extends the :ref:`dam_v001_restriction_enabled` example of application
model |dam_v001|.  It confirms that the restriction on releasing water when there is
little inflow works as explained for model |dam_v001|.  In addition, it shows that
|dam_v005| uses sequence |MissingRemoteRelease| to indicate when the |ActualRelease| is
smaller than the estimated |RequiredRemoteRelease| and passes this information to the
`demand` node:

>>> inflow.sequences.sim.series[:10] = 1.0
>>> inflow.sequences.sim.series[10:] = 0.1
>>> actual_supply.sequences.sim.series = 0.0
>>> actual_relief.sequences.sim.series = 0.0
>>> neardischargeminimumtolerance(0.0)

.. integration-test::

    >>> test("dam_v005_restriction_enabled")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   demand | inflow | natural |  outflow |   remote | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.017282 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.839983 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |             0.2 |             0.2 |      0.199917 |                  0.0 |            0.0 | 0.199917 |    0.069127 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.8 | 0.199917 | 1.839983 |             1.0 |
    | 02.01. |   0.034562 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.819967 |               1.640067 |          0.0 |     -0.439983 |              0.008616 |                 5.0 |                  1.0 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |    0.138247 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.7 |      0.2 | 1.819967 |             1.0 |
    | 03.01. |   0.051842 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.779975 |               1.619967 |          0.0 |     -0.419967 |              0.010321 |                 5.0 |             0.999999 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |    0.207367 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.6 |      0.2 | 1.779975 |        0.999999 |
    | 04.01. |   0.069122 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.699992 |               1.579975 |          0.0 |     -0.379975 |              0.014769 |                 5.0 |             0.999994 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |    0.276487 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.5 |      0.2 | 1.699992 |        0.999994 |
    | 05.01. |   0.086402 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |                  1.6 |               1.499992 |          0.0 |     -0.299992 |              0.029846 |                 5.0 |             0.999971 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |    0.345607 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.4 |      0.2 |      1.6 |        0.999971 |
    | 06.01. |   0.103682 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |                  1.5 |                    1.4 |          0.0 |          -0.2 |              0.068641 |                 5.0 |             0.999857 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |    0.414727 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.3 |      0.2 |      1.5 |        0.999857 |
    | 07.01. |   0.120042 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.408516 |                    1.3 |          0.1 |          -0.1 |              0.242578 |                 5.0 |             0.999357 |        0.242578 |        0.242578 |      0.242578 |                  0.0 |            0.0 | 0.242578 |    0.480168 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.2 | 0.242578 | 1.408516 |        0.999357 |
    | 08.01. |   0.131398 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             1.371888 |               1.165937 |     0.234063 |     -0.008516 |              0.474285 |                 5.0 |             0.998176 |        0.474285 |        0.474285 |      0.474285 |                  0.0 |            0.0 | 0.474285 |     0.52559 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.1 | 0.474285 | 1.371888 |        0.998176 |
    | 09.01. |   0.136052 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              1.43939 |               0.897603 |     0.502397 |      0.028112 |              0.784512 |                 5.0 |             0.997205 |        0.784512 |        0.784512 |      0.784512 |                  0.0 |            0.0 | 0.784512 |    0.544208 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.0 | 0.784512 |  1.43939 |        0.997205 |
    | 10.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |              1.67042 |               0.654878 |     0.745122 |      -0.03939 |               0.95036 |                 5.0 |             0.996916 |         0.95036 |         0.95036 |       0.95036 |                  0.0 |            0.0 |  0.95036 |    0.548497 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.0 |  0.95036 |  1.67042 |        0.996916 |
    | 11.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |             1.682926 |               0.720061 |     0.679939 |      -0.27042 |               0.71839 |                 5.0 |             0.996916 |         0.71839 |             0.1 |           0.1 |              0.61839 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 |  0.61839 |    0.1 |     1.0 |      0.1 | 1.682926 |        0.996916 |
    | 12.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |             1.423559 |               1.582926 |          0.0 |     -0.282926 |              0.034564 |                 5.0 |             0.996916 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.0 |      0.1 | 1.423559 |        0.996916 |
    | 13.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |             1.285036 |               1.323559 |     0.076441 |     -0.023559 |              0.299482 |                 5.0 |             0.996916 |        0.299482 |             0.1 |           0.1 |             0.199482 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 | 0.199482 |    0.1 |     1.1 |      0.1 | 1.285036 |        0.996916 |
    | 14.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  1.3 |               1.185036 |     0.214964 |      0.114964 |              0.585979 |                 5.0 |             0.996916 |        0.585979 |             0.1 |           0.1 |             0.485979 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 | 0.485979 |    0.1 |     1.2 |      0.1 |      1.3 |        0.996916 |
    | 15.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  1.4 |                    1.2 |          0.2 |           0.1 |              0.557422 |                 5.0 |             0.996916 |        0.557422 |             0.1 |           0.1 |             0.457422 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 | 0.457422 |    0.1 |     1.3 |      0.1 |      1.4 |        0.996916 |
    | 16.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  1.5 |                    1.3 |          0.1 |           0.0 |                  0.35 |                 5.0 |             0.996916 |            0.35 |             0.1 |           0.1 |                 0.25 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 |     0.25 |    0.1 |     1.4 |      0.1 |      1.5 |        0.996916 |
    | 17.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  1.6 |                    1.4 |          0.0 |          -0.1 |              0.142578 |                 5.0 |             0.996916 |             0.2 |             0.1 |           0.1 |             0.042578 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 | 0.042578 |    0.1 |     1.5 |      0.1 |      1.6 |        0.996916 |
    | 18.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  1.7 |                    1.5 |          0.0 |          -0.2 |              0.068641 |                 5.0 |             0.996916 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.6 |      0.1 |      1.7 |        0.996916 |
    | 19.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  1.8 |                    1.6 |          0.0 |          -0.3 |              0.029844 |                 5.0 |             0.996916 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.7 |      0.1 |      1.8 |        0.996916 |
    | 20.01. |   0.137124 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.1 |                  1.9 |                    1.7 |          0.0 |          -0.4 |              0.012348 |                 5.0 |             0.996916 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |    0.548497 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.8 |      0.1 |      1.9 |        0.996916 |

.. _dam_v005_smooth_stage_minimum:

smooth stage minimum
____________________

This example extends the :ref:`dam_v001_smooth_stage_minimum` example of application
model |dam_v001|.  We update parameters |WaterLevelMinimumThreshold| and
|WaterLevelMinimumTolerance|, as well as the time series of the "normal" inflow,
accordingly:

>>> neardischargeminimumthreshold(0.0)
>>> waterlevelminimumtolerance(0.01)
>>> waterlevelminimumthreshold(0.005)
>>> inflow.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)

There is also a perfect agreement between |dam_v001| and |dam_v005| for the given case
where the available water storage is too limited to reease enough discharge:

.. integration-test::

    >>> test("dam_v005_smooth_stage_minimum")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation |   inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   demand |   inflow | natural |  outflow |   remote | required_supply |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.004295 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |      0.2 |             1.800227 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |           0.005 |           0.005 |      0.001137 |             0.003863 |            0.0 | 0.001137 |    0.017182 |           0.0 |           0.0 |            5.0 | 0.003863 |      0.2 |     1.8 | 0.001137 | 1.800227 |             1.0 |
    | 02.01. |    0.00822 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.189474 |             1.702016 |                1.79909 |          0.0 |     -0.400227 |              0.012323 |                 5.0 |                  1.0 |        0.012323 |        0.012323 |      0.007804 |             0.004519 |            0.0 | 0.007804 |    0.032878 |           0.0 |           0.0 |            5.0 | 0.004519 | 0.189474 |     1.7 | 0.007804 | 1.702016 |             1.0 |
    | 03.01. |   0.011516 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.178947 |             1.608725 |               1.694212 |          0.0 |     -0.302016 |              0.029329 |                 5.0 |                  1.0 |        0.029329 |        0.029329 |      0.026311 |             0.003018 |            0.0 | 0.026311 |    0.046066 |           0.0 |           0.0 |            5.0 | 0.003018 | 0.178947 |     1.6 | 0.026311 | 1.608725 |             1.0 |
    | 04.01. |   0.013813 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.168421 |             1.525402 |               1.582414 |          0.0 |     -0.208725 |              0.064029 |                 5.0 |                  1.0 |        0.064029 |        0.064029 |      0.062116 |             0.001913 |            0.0 | 0.062116 |    0.055251 |           0.0 |           0.0 |            5.0 | 0.001913 | 0.168421 |     1.5 | 0.062116 | 1.525402 |             1.0 |
    | 05.01. |   0.014668 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.157895 |             1.457183 |               1.463286 |          0.0 |     -0.125402 |              0.120018 |                 5.0 |                  1.0 |        0.120018 |        0.120018 |      0.118314 |             0.001704 |            0.0 | 0.118314 |     0.05867 |           0.0 |           0.0 |            5.0 | 0.001704 | 0.157895 |     1.4 | 0.118314 | 1.457183 |             1.0 |
    | 06.01. |    0.01262 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.147368 |             1.417026 |               1.338869 |     0.061131 |     -0.057183 |              0.246912 |                 5.0 |                  1.0 |        0.246912 |        0.246912 |      0.242169 |             0.004743 |            0.0 | 0.242169 |     0.05048 |           0.0 |           0.0 |            5.0 | 0.004743 | 0.147368 |     1.3 | 0.242169 | 1.417026 |             1.0 |
    | 07.01. |      0.007 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.136842 |             1.417974 |               1.174856 |     0.225144 |     -0.017026 |              0.455625 |                 5.0 |                  1.0 |        0.455625 |        0.455625 |      0.397003 |             0.058622 |            0.0 | 0.397003 |    0.028002 |           0.0 |           0.0 |            5.0 | 0.058622 | 0.136842 |     1.2 | 0.397003 | 1.417974 |             1.0 |
    | 08.01. |   0.003446 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.126316 |             1.401455 |               1.020971 |     0.379029 |     -0.017974 |              0.608427 |                 5.0 |                  1.0 |        0.608427 |        0.608427 |      0.290857 |             0.317571 |            0.0 | 0.290857 |    0.013785 |           0.0 |           0.0 |            5.0 | 0.317571 | 0.126316 |     1.1 | 0.290857 | 1.401455 |             1.0 |
    | 09.01. |   0.002653 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.115789 |             1.290165 |               1.110598 |     0.289402 |     -0.001455 |              0.537731 |                 5.0 |                  1.0 |        0.537731 |        0.537731 |      0.152525 |             0.385206 |            0.0 | 0.152525 |    0.010611 |           0.0 |           0.0 |            5.0 | 0.385206 | 0.115789 |     1.0 | 0.152525 | 1.290165 |             1.0 |
    | 10.01. |   0.001943 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.105263 |             1.215588 |               1.137641 |     0.262359 |      0.109835 |              0.628811 |                 5.0 |                  1.0 |        0.628811 |        0.628811 |      0.138106 |             0.490706 |            0.0 | 0.138106 |    0.007774 |           0.0 |           0.0 |            5.0 | 0.490706 | 0.105263 |     1.0 | 0.138106 | 1.215588 |             1.0 |
    | 11.01. |   0.001257 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.094737 |             1.155391 |               1.077483 |     0.322517 |      0.184412 |              0.744943 |                 5.0 |                  1.0 |        0.744943 |        0.744943 |      0.126527 |             0.618417 |            0.0 | 0.126527 |    0.005027 |           0.0 |           0.0 |            5.0 | 0.618417 | 0.094737 |     1.0 | 0.126527 | 1.155391 |             1.0 |
    | 12.01. |   0.000695 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.084211 |             1.129338 |               1.028864 |     0.371136 |      0.244609 |              0.823376 |                 5.0 |                  1.0 |        0.823376 |        0.823376 |      0.110214 |             0.713162 |            0.0 | 0.110214 |     0.00278 |           0.0 |           0.0 |            5.0 | 0.713162 | 0.084211 |     1.0 | 0.110214 | 1.129338 |             1.0 |
    | 13.01. |   0.000276 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.073684 |             1.214467 |               1.019124 |     0.380876 |      0.270662 |              0.842505 |                 5.0 |                  1.0 |        0.842505 |        0.842505 |      0.093065 |              0.74944 |            0.0 | 0.093065 |    0.001106 |           0.0 |           0.0 |            5.0 |  0.74944 | 0.073684 |     1.1 | 0.093065 | 1.214467 |             1.0 |
    | 14.01. |   0.000137 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.063158 |             1.296867 |               1.121402 |     0.278598 |      0.185533 |              0.701697 |                 5.0 |                  1.0 |        0.701697 |        0.701697 |      0.069621 |             0.632076 |            0.0 | 0.069621 |    0.000547 |           0.0 |           0.0 |            5.0 | 0.632076 | 0.063158 |     1.2 | 0.069621 | 1.296867 |             1.0 |
    | 15.01. |   0.000156 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.052632 |              1.37714 |               1.227246 |     0.172754 |      0.103133 |              0.533092 |                 5.0 |                  1.0 |        0.533092 |        0.533092 |      0.051753 |             0.481339 |            0.0 | 0.051753 |    0.000623 |           0.0 |           0.0 |            5.0 | 0.481339 | 0.052632 |     1.3 | 0.051753 |  1.37714 |             1.0 |
    | 16.01. |   0.000303 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.042105 |             1.457954 |               1.325387 |     0.074613 |       0.02286 |              0.350778 |                 5.0 |                  1.0 |        0.350778 |        0.350778 |      0.035299 |             0.315479 |            0.0 | 0.035299 |    0.001211 |           0.0 |           0.0 |            5.0 | 0.315479 | 0.042105 |     1.4 | 0.035299 | 1.457954 |             1.0 |
    | 17.01. |   0.000549 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.031579 |             1.540644 |               1.422655 |          0.0 |     -0.057954 |              0.184954 |                 5.0 |                  1.0 |        0.184954 |        0.184954 |      0.020178 |             0.164776 |            0.0 | 0.020178 |    0.002196 |           0.0 |           0.0 |            5.0 | 0.164776 | 0.031579 |     1.5 | 0.020178 | 1.540644 |             1.0 |
    | 18.01. |   0.000727 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.021053 |             1.626397 |               1.520465 |          0.0 |     -0.140644 |              0.107711 |                 5.0 |                  1.0 |        0.107711 |        0.107711 |      0.012801 |              0.09491 |            0.0 | 0.012801 |    0.002909 |           0.0 |           0.0 |            5.0 |  0.09491 | 0.021053 |     1.6 | 0.012801 | 1.626397 |             1.0 |
    | 19.01. |   0.000805 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 | 0.010526 |             1.716092 |               1.613595 |          0.0 |     -0.226397 |              0.055496 |                 5.0 |                  1.0 |        0.055496 |        0.055496 |      0.006941 |             0.048556 |            0.0 | 0.006941 |    0.003219 |           0.0 |           0.0 |            5.0 | 0.048556 | 0.010526 |     1.7 | 0.006941 | 1.716092 |             1.0 |
    | 20.01. |   0.000769 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |      0.0 |             1.808962 |               1.709151 |          0.0 |     -0.316092 |              0.025954 |                 5.0 |                  1.0 |        0.025954 |        0.012977 |      0.001636 |             0.024318 |            0.0 | 0.001636 |    0.003078 |           0.0 |           0.0 |            5.0 | 0.024318 |      0.0 |     1.8 | 0.001636 | 1.808962 |             1.0 |

.. _dam_v005_evaporation:

evaporation
___________

This example repeats the :ref:`dam_v001_evaporation` example of application model
|dam_v001|.  We add an |evap_io| submodel and update the time series of potential
evaporation accordingly:

>>> with model.add_pemodel_v1("evap_io") as pemodel:
...     evapotranspirationfactor(1.0)
>>> pemodel.prepare_inputseries()
>>> pemodel.sequences.inputs.referenceevapotranspiration.series = 10 * [1.0] + 10 * [5.0]

All internal evaporation-related results agree with the ones of |dam_v001| exactly:

.. integration-test::

    >>> test("dam_v005_evaporation")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation |   inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   demand |   inflow | natural |  outflow |   remote | required_supply |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.003964 |           0.0 |                   0.0 |                  1.0 |               0.016 |          0.015403 |      0.2 |             1.800214 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |           0.005 |           0.005 |      0.001069 |             0.003931 |            0.0 | 0.001069 |    0.015857 |           0.0 |           0.0 |            5.0 | 0.003931 |      0.2 |     1.8 | 0.001069 | 1.800214 |             1.0 |
    | 02.01. |   0.007488 |           0.0 |                   0.0 |                  1.0 |              0.0192 |            0.0192 | 0.189474 |             1.701857 |               1.799145 |          0.0 |     -0.400214 |              0.012324 |                 5.0 |                  1.0 |        0.012324 |        0.012324 |      0.007145 |              0.00518 |            0.0 | 0.007145 |    0.029951 |           0.0 |           0.0 |            5.0 |  0.00518 | 0.189474 |     1.7 | 0.007145 | 1.701857 |             1.0 |
    | 03.01. |   0.010383 |           0.0 |                   0.0 |                  1.0 |             0.01984 |           0.01984 | 0.178947 |             1.608191 |               1.694712 |          0.0 |     -0.301857 |              0.029369 |                 5.0 |                  1.0 |        0.029369 |        0.029369 |      0.025061 |             0.004308 |            0.0 | 0.025061 |    0.041533 |           0.0 |           0.0 |            5.0 | 0.004308 | 0.178947 |     1.6 | 0.025061 | 1.608191 |             1.0 |
    | 04.01. |   0.012274 |           0.0 |                   0.0 |                  1.0 |            0.019968 |          0.019968 | 0.168421 |             1.524454 |                1.58313 |          0.0 |     -0.208191 |              0.064304 |                 5.0 |                  1.0 |        0.064304 |        0.064304 |      0.060894 |              0.00341 |            0.0 | 0.060894 |    0.049098 |           0.0 |           0.0 |            5.0 |  0.00341 | 0.168421 |     1.5 | 0.060894 | 1.524454 |             1.0 |
    | 05.01. |   0.012724 |           0.0 |                   0.0 |                  1.0 |            0.019994 |          0.019994 | 0.157895 |             1.456007 |               1.463559 |          0.0 |     -0.124454 |              0.120816 |                 5.0 |                  1.0 |        0.120816 |        0.120816 |       0.11708 |             0.003735 |            0.0 |  0.11708 |    0.050897 |           0.0 |           0.0 |            5.0 | 0.003735 | 0.157895 |     1.4 |  0.11708 | 1.456007 |             1.0 |
    | 06.01. |   0.010381 |           0.0 |                   0.0 |                  1.0 |            0.019999 |          0.019999 | 0.147368 |             1.414779 |               1.338926 |     0.061074 |     -0.056007 |              0.248118 |                 5.0 |                  1.0 |        0.248118 |        0.248118 |      0.235862 |             0.012256 |            0.0 | 0.235862 |    0.041523 |           0.0 |           0.0 |            5.0 | 0.012256 | 0.147368 |     1.3 | 0.235862 | 1.414779 |             1.0 |
    | 07.01. |   0.005528 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 | 0.136842 |             1.403864 |               1.178917 |     0.221083 |     -0.014779 |              0.454132 |                 5.0 |                  1.0 |        0.454132 |        0.454132 |      0.341526 |             0.112606 |            0.0 | 0.341526 |     0.02211 |           0.0 |           0.0 |            5.0 | 0.112606 | 0.136842 |     1.2 | 0.341526 | 1.403864 |             1.0 |
    | 08.01. |   0.002963 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 | 0.126316 |             1.364088 |               1.062338 |     0.337662 |     -0.003864 |              0.583224 |                 5.0 |                  1.0 |        0.583224 |        0.583224 |      0.225053 |             0.358172 |            0.0 | 0.225053 |    0.011851 |           0.0 |           0.0 |            5.0 | 0.358172 | 0.126316 |     1.1 | 0.225053 | 1.364088 |             1.0 |
    | 09.01. |   0.002161 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 | 0.115789 |              1.24265 |               1.139035 |     0.260965 |      0.035912 |               0.55185 |                 5.0 |                  1.0 |         0.55185 |         0.55185 |      0.132924 |             0.418926 |            0.0 | 0.132924 |    0.008643 |           0.0 |           0.0 |            5.0 | 0.418926 | 0.115789 |     1.0 | 0.132924 |  1.24265 |             1.0 |
    | 10.01. |   0.001322 |           0.0 |                   0.0 |                  1.0 |                0.02 |          0.019985 | 0.105263 |             1.179664 |               1.109726 |     0.290274 |       0.15735 |              0.694972 |                 5.0 |                  1.0 |        0.694972 |        0.694972 |      0.124131 |             0.570841 |            0.0 | 0.124131 |    0.005286 |           0.0 |           0.0 |            5.0 | 0.570841 | 0.105263 |     1.0 | 0.124131 | 1.179664 |             1.0 |
    | 11.01. |  -0.000009 |           0.0 |                   0.0 |                  5.0 |               0.084 |          0.067788 | 0.094737 |             1.129746 |               1.055533 |     0.344467 |      0.220336 |              0.786162 |                 5.0 |                  1.0 |        0.786162 |        0.786162 |      0.088555 |             0.697607 |            0.0 | 0.088555 |   -0.000037 |           0.0 |           0.0 |            5.0 | 0.697607 | 0.094737 |     1.0 | 0.088555 | 1.129746 |             1.0 |
    | 12.01. |  -0.000277 |           0.0 |                   0.0 |                  5.0 |              0.0968 |          0.027792 | 0.084211 |              1.09972 |               1.041191 |     0.358809 |      0.270254 |              0.820305 |                 5.0 |                  1.0 |        0.820305 |        0.820305 |       0.06883 |             0.751475 |            0.0 |  0.06883 |   -0.001109 |           0.0 |           0.0 |            5.0 | 0.751475 | 0.084211 |     1.0 |  0.06883 |  1.09972 |             1.0 |
    | 13.01. |  -0.000428 |           0.0 |                   0.0 |                  5.0 |             0.09936 |           0.01519 | 0.073684 |             1.179604 |               1.030889 |     0.369111 |       0.30028 |              0.839339 |                 5.0 |                  1.0 |        0.839339 |        0.839339 |      0.065462 |             0.773877 |            0.0 | 0.065462 |   -0.001711 |           0.0 |           0.0 |            5.0 | 0.773877 | 0.073684 |     1.1 | 0.065462 | 1.179604 |             1.0 |
    | 14.01. |   -0.00048 |           0.0 |                   0.0 |                  5.0 |            0.099872 |          0.010814 | 0.063158 |             1.266641 |               1.114142 |     0.285858 |      0.220396 |              0.727582 |                 5.0 |                  1.0 |        0.727582 |        0.727582 |      0.054758 |             0.672824 |            0.0 | 0.054758 |   -0.001919 |           0.0 |           0.0 |            5.0 | 0.672824 | 0.063158 |     1.2 | 0.054758 | 1.266641 |             1.0 |
    | 15.01. |  -0.000481 |           0.0 |                   0.0 |                  5.0 |            0.099974 |          0.009855 | 0.052632 |             1.356992 |               1.211883 |     0.188117 |      0.133359 |              0.574641 |                 5.0 |                  1.0 |        0.574641 |        0.574641 |      0.042837 |             0.531804 |            0.0 | 0.042837 |   -0.001925 |           0.0 |           0.0 |            5.0 | 0.531804 | 0.052632 |     1.3 | 0.042837 | 1.356992 |             1.0 |
    | 16.01. |  -0.000436 |           0.0 |                   0.0 |                  5.0 |            0.099995 |          0.011026 | 0.042105 |             1.445909 |               1.314155 |     0.085845 |      0.043008 |              0.384618 |                 5.0 |                  1.0 |        0.384618 |        0.384618 |      0.029002 |             0.355616 |            0.0 | 0.029002 |   -0.001745 |           0.0 |           0.0 |            5.0 | 0.355616 | 0.042105 |     1.4 | 0.029002 | 1.445909 |             1.0 |
    | 17.01. |  -0.000379 |           0.0 |                   0.0 |                  5.0 |            0.099999 |          0.013667 | 0.031579 |             1.532982 |               1.416907 |          0.0 |     -0.045909 |               0.19803 |                 5.0 |                  1.0 |         0.19803 |         0.19803 |      0.015273 |             0.182757 |            0.0 | 0.015273 |   -0.001517 |           0.0 |           0.0 |            5.0 | 0.182757 | 0.031579 |     1.5 | 0.015273 | 1.532982 |             1.0 |
    | 18.01. |  -0.000412 |           0.0 |                   0.0 |                  5.0 |                 0.1 |          0.013795 | 0.021053 |             1.620851 |               1.517709 |          0.0 |     -0.132982 |               0.11378 |                 5.0 |                  1.0 |         0.11378 |         0.11378 |      0.008785 |             0.104995 |            0.0 | 0.008785 |   -0.001649 |           0.0 |           0.0 |            5.0 | 0.104995 | 0.021053 |     1.6 | 0.008785 | 1.620851 |             1.0 |
    | 19.01. |  -0.000506 |           0.0 |                   0.0 |                  5.0 |                 0.1 |          0.010518 | 0.010526 |             1.711867 |               1.612065 |          0.0 |     -0.220851 |              0.058061 |                 5.0 |                  1.0 |        0.058061 |        0.058061 |      0.004355 |             0.053706 |            0.0 | 0.004355 |   -0.002025 |           0.0 |           0.0 |            5.0 | 0.053706 | 0.010526 |     1.7 | 0.004355 | 1.711867 |             1.0 |
    | 20.01. |  -0.000662 |           0.0 |                   0.0 |                  5.0 |                 0.1 |          0.006255 |      0.0 |             1.806096 |               1.707512 |          0.0 |     -0.311867 |              0.026927 |                 5.0 |                  1.0 |        0.026927 |        0.013463 |      0.000957 |              0.02597 |            0.0 | 0.000957 |   -0.002648 |           0.0 |           0.0 |            5.0 |  0.02597 |      0.0 |     1.8 | 0.000957 | 1.806096 |             1.0 |

>>> del model.pemodel

.. _dam_v005_flood_retention:

flood retention
_______________

This example repeats the :ref:`dam_v001_flood_retention` example of application model
|dam_v001|.  We use the same parameter and input time series configuration:

>>> remotedischargeminimum(0.0)
>>> remotedischargesafety(0.0)
>>> waterlevelminimumthreshold(0.0)
>>> waterlevelminimumtolerance(0.0)
>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys= [0.0, 2.5]))
>>> neardischargeminimumthreshold(0.0)
>>> with model.add_precipmodel_v2("meteo_precip_io") as precipmodel:
...     precipitationfactor(1.0)
>>> precipmodel.prepare_inputseries()
>>> precipmodel.sequences.inputs.precipitation.series = [
...     0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inflow.sequences.sim.series = [0.0, 0.0, 5.0, 9.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> test.inits.loggedtotalremotedischarge = 1.0
>>> natural.sequences.sim.series = 1.0

The following test results show that |dam_v005| reproduces the water levels and outflow
values calculated by |dam_v001| precisely.  Furthermore, they illustrate the estimation
of |AllowedRemoteRelief| based on the current water level, which is functionally
similar to the one of |RequiredRemoteSupply| discussed in the
:ref:`dam_v005_smooth_near_minimum` example:

.. integration-test::

    >>> test("dam_v005_flood_retention")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | demand | inflow | natural |  outflow |   remote | required_supply |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |                 5.0 |                  1.0 |             0.0 |             0.0 |           0.0 |                  0.0 |            0.0 |      0.0 |         0.0 |           0.0 |           0.0 |            5.0 |    0.0 |    0.0 |     1.0 |      0.0 |      1.0 |             1.0 |
    | 02.01. |   0.021027 |          50.0 |                   1.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             1.005304 |                    1.0 |          0.0 |          -1.0 |                   0.0 |                 5.0 |                  1.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.026521 | 0.026521 |    0.084109 |           0.0 |           0.0 |            5.0 |    0.0 |    0.0 |     1.0 | 0.026521 | 1.005304 |             1.0 |
    | 03.01. |   0.125058 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    5.0 |             1.047364 |               0.978784 |          0.0 |     -1.005304 |                   0.0 |                 5.0 |              0.99898 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.183777 | 0.183777 |     0.50023 |           0.0 |           0.0 |            5.0 |    0.0 |    5.0 |     1.0 | 0.183777 | 1.047364 |         0.99898 |
    | 04.01. |   0.307728 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    9.0 |             1.190074 |               0.863587 |          0.0 |     -1.047364 |                   0.0 |                 5.0 |              0.00005 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.543038 | 0.543038 |    1.230912 |           0.0 |           0.0 |            5.0 |    0.0 |    9.0 |     1.0 | 0.543038 | 1.190074 |         0.00005 |
    | 05.01. |   0.459769 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    8.0 |             1.467216 |               0.647037 |          0.0 |     -1.190074 |                   0.0 |            4.879054 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.961082 | 0.961082 |    1.839074 |           0.0 |           0.0 |       4.879054 |    0.0 |    8.0 |     1.0 | 0.961082 | 1.467216 |             0.0 |
    | 06.01. |   0.540735 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    5.0 |              1.81603 |               0.506135 |          0.0 |     -1.467216 |                   0.0 |            0.115599 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.251541 | 1.251541 |    2.162941 |           0.0 |           0.0 |       0.115599 |    0.0 |    5.0 |     1.0 | 1.251541 |  1.81603 |             0.0 |
    | 07.01. |   0.575391 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |             2.122354 |               0.564489 |          0.0 |      -1.81603 |                   0.0 |            0.004892 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.395548 | 1.395548 |    2.301566 |           0.0 |           0.0 |       0.004892 |    0.0 |    3.0 |     1.0 | 1.395548 | 2.122354 |             0.0 |
    | 08.01. |   0.587199 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |             2.320464 |               0.726806 |          0.0 |     -2.122354 |                   0.0 |            0.001654 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.453371 | 1.453371 |    2.348795 |           0.0 |           0.0 |       0.001654 |    0.0 |    2.0 |     1.0 | 1.453371 | 2.320464 |             0.0 |
    | 09.01. |   0.577358 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |             2.416284 |               0.867093 |          0.0 |     -2.320464 |                   0.0 |            0.004084 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.455585 | 1.455585 |    2.309432 |           0.0 |           0.0 |       0.004084 |    0.0 |    1.0 |     1.0 | 1.455585 | 2.416284 |             0.0 |
    | 10.01. |   0.547008 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.438823 |               0.960699 |          0.0 |     -2.416284 |                   0.0 |             0.06562 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.405115 | 1.405115 |     2.18803 |           0.0 |           0.0 |        0.06562 |    0.0 |    0.0 |     1.0 | 1.405115 | 2.438823 |             0.0 |
    | 11.01. |   0.518253 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.410309 |               1.033708 |          0.0 |     -2.438823 |                   0.0 |            0.787168 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.331251 | 1.331251 |     2.07301 |           0.0 |           0.0 |       0.787168 |    0.0 |    0.0 |     1.0 | 1.331251 | 2.410309 |             0.0 |
    | 12.01. |   0.491009 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.351848 |               1.079058 |          0.0 |     -2.410309 |                   0.0 |            3.477848 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |        1.26127 |  1.26127 |    1.964036 |           0.0 |           0.0 |       3.477848 |    0.0 |    0.0 |     1.0 |  1.26127 | 2.351848 |             0.0 |
    | 13.01. |   0.465198 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.283389 |               1.090577 |          0.0 |     -2.351848 |                   0.0 |            4.803872 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.194968 | 1.194968 |    1.860791 |           0.0 |           0.0 |       4.803872 |    0.0 |    0.0 |     1.0 | 1.194968 | 2.283389 |             0.0 |
    | 14.01. |   0.440743 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.215924 |               1.088421 |          0.0 |     -2.283389 |                   0.0 |            4.978521 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.132151 | 1.132151 |    1.762973 |           0.0 |           0.0 |       4.978521 |    0.0 |    0.0 |     1.0 | 1.132151 | 2.215924 |             0.0 |
    | 15.01. |   0.417574 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.152005 |               1.083773 |          0.0 |     -2.215924 |                   0.0 |            4.997436 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.072636 | 1.072636 |    1.670297 |           0.0 |           0.0 |       4.997436 |    0.0 |    0.0 |     1.0 | 1.072636 | 2.152005 |             0.0 |
    | 16.01. |   0.395623 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.091447 |               1.079369 |          0.0 |     -2.152005 |                   0.0 |            4.999659 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |        1.01625 |  1.01625 |    1.582493 |           0.0 |           0.0 |       4.999659 |    0.0 |    0.0 |     1.0 |  1.01625 | 2.091447 |             0.0 |
    | 17.01. |   0.374826 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             2.034072 |               1.075197 |          0.0 |     -2.091447 |                   0.0 |             4.99995 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.962828 | 0.962828 |    1.499305 |           0.0 |           0.0 |        4.99995 |    0.0 |    0.0 |     1.0 | 0.962828 | 2.034072 |             0.0 |
    | 18.01. |   0.355122 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             1.979713 |               1.071244 |          0.0 |     -2.034072 |                   0.0 |            4.999992 |             0.000001 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.912214 | 0.912214 |     1.42049 |           0.0 |           0.0 |       4.999992 |    0.0 |    0.0 |     1.0 | 0.912214 | 1.979713 |        0.000001 |
    | 19.01. |   0.336454 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             1.928211 |               1.067499 |          0.0 |     -1.979713 |                   0.0 |            4.999999 |             0.000004 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.864261 | 0.864261 |    1.345818 |           0.0 |           0.0 |       4.999999 |    0.0 |    0.0 |     1.0 | 0.864261 | 1.928211 |        0.000004 |
    | 20.01. |   0.318768 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |             1.879417 |                1.06395 |          0.0 |     -1.928211 |                   0.0 |                 5.0 |             0.000018 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.818829 | 0.818829 |    1.275071 |           0.0 |           0.0 |            5.0 |    0.0 |    0.0 |     1.0 | 0.818829 | 1.879417 |        0.000018 |
"""

# import...

# ...from HydPy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.core import modeltools
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.exe.modelimports import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(dam_model.Main_PrecipModel_V2, dam_model.Main_PEModel_V1):
    """Version 5 of HydPy-Dam."""

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
        dam_model.Pic_Inflow_V2,
        dam_model.Calc_NaturalRemoteDischarge_V1,
        dam_model.Calc_RemoteDemand_V1,
        dam_model.Calc_RemoteFailure_V1,
        dam_model.Calc_RequiredRemoteRelease_V1,
        dam_model.Calc_RequiredRelease_V1,
        dam_model.Calc_TargetedRelease_V1,
    )
    RECEIVER_METHODS = (
        dam_model.Pic_TotalRemoteDischarge_V1,
        dam_model.Update_LoggedTotalRemoteDischarge_V1,
    )
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V2,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_ActualRelease_V1,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_Outflow_V1,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V1,)
    OUTLET_METHODS = (
        dam_model.Calc_WaterLevel_V1,
        dam_model.Pass_Outflow_V1,
        dam_model.Update_LoggedOutflow_V1,
    )
    SENDER_METHODS = (
        dam_model.Calc_MissingRemoteRelease_V1,
        dam_model.Pass_MissingRemoteRelease_V1,
        dam_model.Calc_AllowedRemoteRelief_V2,
        dam_model.Pass_AllowedRemoteRelief_V1,
        dam_model.Calc_RequiredRemoteSupply_V1,
        dam_model.Pass_RequiredRemoteSupply_V1,
    )
    SUBMODELINTERFACES = (precipinterfaces.PrecipModel_V2, petinterfaces.PETModel_V1)
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)


tester = Tester()
cythonizer = Cythonizer()
