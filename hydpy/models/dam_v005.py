# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Version 5 application model of HydPy-Dam.

Application model |dam_v005| extends |dam_v001| with two features enabling
collaboration with other dam models for better drought and flood prevention.

Like |dam_v001|, |dam_v005| tries to increase the discharge at a remote location in the
channel downstream during low flow conditions and sometimes fails due to its limited
storage content.  One additional feature of |dam_v005| is that it passes the information
on its anticipated failure to another remote location.  This information enables other
models to jump in when necessary.

The second additional feature of |dam_v005| is that it receives input from two
additional inlet nodes, one passing "supply discharge" and the other one "relief
discharge".  We understand "supply discharge" as water delivered from a remote location
to increase the storage content of |dam_v005| when necessary (during droughts).  In
contrast, relief discharge serves to relieve the other location (possibly another dam)
during floods.  |dam_v005| calculates both the desirable supply discharge and the
acceptable relief discharge and passes that information to a single or two separate
remote locations.

The following explanations focus on these differences.  For further information on using
|dam_v005|, please read the documentation on model |dam_v001|.  Besides that, see the
documentation on |dam_v002| and |dam_v004|, which are possible counterparts for
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

|dam_v005| needs to connect to two additional inlet nodes and also to three sender
nodes.  The input nodes `actual_supply` and `actual_relief` handle the actual supply
and relief discharge from remote locations.  The sender nodes `required_supply` and
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
use cases of |dam_v005|.  However, we do not want to bloat up the already scenario
setting further.  Hence, instead of dynamically calculating the remote locations'
discharges, we prefer to apply predefined discharge time series.

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

We define identical time series for |dam_inputs.Precipitation|,
|dam_inputs.Evaporation|, and the subcatchment's discharge time series:

>>> inputs.precipitation.series = 0.0
>>> inputs.evaporation.series = 0.0
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
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | demand |   inflow | natural |  outflow |   remote | required_supply |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017242 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.840351 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |        0.210526 |        0.210526 |      0.201754 |                  0.0 |            0.0 | 0.201754 |    0.068968 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.8 | 0.201754 | 1.840351 |             1.0 |
    | 02.01. |           0.0 |         0.0 |   0.034286 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.822886 |               1.638597 |          0.0 |     -0.440351 |              0.008588 |                 5.0 |                  1.0 |         0.21092 |         0.21092 |       0.21092 |                  0.0 |            0.0 |  0.21092 |    0.137145 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.7 |  0.21092 | 1.822886 |             1.0 |
    | 03.01. |           0.0 |         0.0 |   0.051327 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.787111 |               1.611966 |          0.0 |     -0.422886 |              0.010053 |                 5.0 |             0.999999 |        0.211084 |        0.211084 |      0.211084 |                  0.0 |            0.0 | 0.211084 |    0.205307 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.6 | 0.211084 | 1.787111 |        0.999999 |
    | 04.01. |           0.0 |         0.0 |   0.068358 |                   0.0 |                 0.0 |               0.0 |    1.0 |              1.71019 |               1.576027 |          0.0 |     -0.387111 |              0.013858 |                 5.0 |             0.999994 |        0.211523 |        0.211523 |      0.211523 |                  0.0 |            0.0 | 0.211523 |    0.273432 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.5 | 0.211523 |  1.71019 |        0.999994 |
    | 05.01. |           0.0 |         0.0 |   0.085353 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.611668 |               1.498667 |          0.0 |      -0.31019 |              0.027322 |                 5.0 |             0.999973 |        0.213209 |        0.213209 |      0.213209 |                  0.0 |            0.0 | 0.213209 |     0.34141 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.4 | 0.213209 | 1.611668 |        0.999973 |
    | 06.01. |           0.0 |         0.0 |   0.102221 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.513658 |               1.398459 |     0.001541 |     -0.211668 |              0.064075 |                 5.0 |             0.999875 |        0.219043 |        0.219043 |      0.219043 |                  0.0 |            0.0 | 0.219043 |    0.408885 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.3 | 0.219043 | 1.513658 |        0.999875 |
    | 07.01. |           0.0 |         0.0 |   0.117699 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.429416 |               1.294615 |     0.105385 |     -0.113658 |              0.235523 |                 5.0 |             0.999481 |        0.283419 |        0.283419 |      0.283419 |                  0.0 |            0.0 | 0.283419 |    0.470798 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.2 | 0.283419 | 1.429416 |        0.999481 |
    | 08.01. |           0.0 |         0.0 |   0.129035 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.395444 |               1.145997 |     0.254003 |     -0.029416 |              0.470414 |                 5.0 |             0.998531 |        0.475212 |        0.475212 |      0.475212 |                  0.0 |            0.0 | 0.475212 |    0.516139 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.1 | 0.475212 | 1.395444 |        0.998531 |
    | 09.01. |           0.0 |         0.0 |   0.134753 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.444071 |               0.920232 |     0.479768 |      0.004556 |              0.735001 |                 5.0 |             0.997518 |        0.735281 |        0.735281 |      0.735281 |                  0.0 |            0.0 | 0.735281 |    0.539011 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.735281 | 1.444071 |        0.997518 |
    | 10.01. |           0.0 |         0.0 |     0.1371 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.643281 |                0.70879 |      0.69121 |     -0.044071 |              0.891263 |                 5.0 |             0.996923 |        0.891315 |        0.891315 |      0.891315 |                  0.0 |            0.0 | 0.891315 |    0.548402 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.891315 | 1.643281 |        0.996923 |
    | 11.01. |           0.0 |         0.0 |   0.143651 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.763981 |               0.751966 |     0.648034 |     -0.243281 |              0.696325 |                 5.0 |             0.994396 |        0.696749 |        0.696749 |      0.696749 |                  0.0 |            0.0 | 0.696749 |    0.574602 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.696749 | 1.763981 |        0.994396 |
    | 12.01. |           0.0 |         0.0 |   0.157336 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.692903 |               1.067232 |     0.332768 |     -0.363981 |              0.349797 |                 5.0 |             0.980562 |        0.366406 |        0.366406 |      0.366406 |                  0.0 |            0.0 | 0.366406 |    0.629345 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.0 | 0.366406 | 1.692903 |        0.980562 |
    | 13.01. |           0.0 |         0.0 |   0.174006 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.590367 |               1.326497 |     0.073503 |     -0.292903 |              0.105231 |                 5.0 |             0.915976 |        0.228241 |        0.228241 |      0.228241 |                  0.0 |            0.0 | 0.228241 |    0.696025 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.1 | 0.228241 | 1.590367 |        0.915976 |
    | 14.01. |           0.0 |         0.0 |   0.190637 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.516904 |               1.362126 |     0.037874 |     -0.190367 |              0.111928 |                 5.0 |              0.70276 |        0.230054 |        0.230054 |      0.230054 |                  0.0 |            0.0 | 0.230054 |    0.762548 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.2 | 0.230054 | 1.516904 |         0.70276 |
    | 15.01. |           0.0 |         0.0 |   0.206051 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.554409 |                1.28685 |      0.11315 |     -0.116904 |              0.240436 |                 5.0 |             0.364442 |        0.286374 |        0.286374 |      0.286374 |                  0.0 |            0.0 | 0.286374 |    0.824205 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.3 | 0.286374 | 1.554409 |        0.364442 |
    | 16.01. |           0.0 |         0.0 |   0.221608 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.662351 |               1.268035 |     0.131965 |     -0.154409 |              0.229369 |                 5.0 |             0.120704 |        0.279807 |        0.279807 |      0.279807 |                  0.0 |            0.0 | 0.279807 |     0.88643 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.4 | 0.279807 | 1.662351 |        0.120704 |
    | 17.01. |           0.0 |         0.0 |   0.238498 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.764451 |               1.382544 |     0.017456 |     -0.262351 |              0.058622 |                 5.0 |             0.028249 |         0.21805 |         0.21805 |       0.21805 |                  0.0 |            0.0 |  0.21805 |    0.953991 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.5 |  0.21805 | 1.764451 |        0.028249 |
    | 18.01. |           0.0 |         0.0 |   0.255521 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.842178 |                 1.5464 |          0.0 |     -0.364451 |              0.016958 |                 5.0 |             0.006045 |        0.211892 |        0.211892 |      0.211892 |                  0.0 |            0.0 | 0.211892 |    1.022083 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.6 | 0.211892 | 1.842178 |        0.006045 |
    | 19.01. |           0.0 |         0.0 |   0.272565 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.920334 |               1.630286 |          0.0 |     -0.442178 |              0.008447 |                 5.0 |             0.001268 |        0.210904 |        0.210904 |      0.210904 |                  0.0 |            0.0 | 0.210904 |    1.090261 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.7 | 0.210904 | 1.920334 |        0.001268 |
    | 20.01. |           0.0 |         0.0 |    0.28962 |                   0.0 |                 0.0 |               0.0 |    1.0 |             2.011822 |               1.709429 |          0.0 |     -0.520334 |              0.004155 |                 5.0 |             0.000265 |        0.210435 |        0.210435 |      0.210435 |                  0.0 |            0.0 | 0.210435 |    1.158479 |      0.333333 |      0.333333 |            5.0 |    0.0 | 0.333333 |     1.8 | 0.210435 | 2.011822 |        0.000265 |

.. _dam_v005_restriction_enabled:

restriction enabled
___________________

This example extends the :ref:`dam_v001_restriction_enabled` example of application
model |dam_v001|.  It confirms that the restriction on releasing water when there is
little inflow works as explained for model |dam_v001|.  In addition, it shows that
|dam_v005| uses sequence |MissingRemoteRelease| to indicate when the |ActualRelease| is
smaller than the estimated |RequiredRemoteRelease| and passes this information the
`demand` node:

>>> inflow.sequences.sim.series[:10] = 1.0
>>> inflow.sequences.sim.series[10:] = 0.1
>>> actual_supply.sequences.sim.series = 0.0
>>> actual_relief.sequences.sim.series = 0.0
>>> neardischargeminimumtolerance(0.0)

.. integration-test::

    >>> test("dam_v005_restriction_enabled")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   demand | inflow | natural |  outflow |   remote | required_supply |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |    0.01746 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.838333 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |             0.2 |             0.2 |      0.191667 |                  0.0 |            0.0 | 0.191667 |     0.06984 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.8 | 0.191667 | 1.838333 |             1.0 |
    | 02.01. |           0.0 |         0.0 |    0.03474 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.816667 |               1.646667 |          0.0 |     -0.438333 |              0.008746 |                 5.0 |                  1.0 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.13896 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.7 |      0.2 | 1.816667 |             1.0 |
    | 03.01. |           0.0 |         0.0 |    0.05202 |                   0.0 |                 0.0 |               0.0 |    1.0 |               1.7775 |               1.616667 |          0.0 |     -0.416667 |              0.010632 |                 5.0 |             0.999999 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.20808 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.6 |      0.2 |   1.7775 |        0.999999 |
    | 04.01. |           0.0 |         0.0 |     0.0693 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.699167 |                 1.5775 |          0.0 |       -0.3775 |              0.015099 |                 5.0 |             0.999994 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |      0.2772 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.5 |      0.2 | 1.699167 |        0.999994 |
    | 05.01. |           0.0 |         0.0 |    0.08658 |                   0.0 |                 0.0 |               0.0 |    1.0 |                  1.6 |               1.499167 |          0.0 |     -0.299167 |               0.03006 |                 5.0 |              0.99997 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.34632 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.4 |      0.2 |      1.6 |         0.99997 |
    | 06.01. |           0.0 |         0.0 |    0.10386 |                   0.0 |                 0.0 |               0.0 |    1.0 |                  1.5 |                    1.4 |          0.0 |          -0.2 |              0.068641 |                 5.0 |             0.999855 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.41544 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.3 |      0.2 |      1.5 |        0.999855 |
    | 07.01. |           0.0 |         0.0 |    0.12022 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.408516 |                    1.3 |          0.1 |          -0.1 |              0.242578 |                 5.0 |             0.999346 |        0.242578 |        0.242578 |      0.242578 |                  0.0 |            0.0 | 0.242578 |    0.480881 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.2 | 0.242578 | 1.408516 |        0.999346 |
    | 08.01. |           0.0 |         0.0 |   0.131576 |                   0.0 |                 0.0 |               0.0 |    1.0 |             1.371888 |               1.165937 |     0.234063 |     -0.008516 |              0.474285 |                 5.0 |             0.998146 |        0.474285 |        0.474285 |      0.474285 |                  0.0 |            0.0 | 0.474285 |    0.526303 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.1 | 0.474285 | 1.371888 |        0.998146 |
    | 09.01. |           0.0 |         0.0 |    0.13623 |                   0.0 |                 0.0 |               0.0 |    1.0 |              1.43939 |               0.897603 |     0.502397 |      0.028112 |              0.784512 |                 5.0 |             0.997159 |        0.784512 |        0.784512 |      0.784512 |                  0.0 |            0.0 | 0.784512 |    0.544921 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.0 | 0.784512 |  1.43939 |        0.997159 |
    | 10.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    1.0 |              1.67042 |               0.654878 |     0.745122 |      -0.03939 |               0.95036 |                 5.0 |             0.996865 |         0.95036 |         0.95036 |       0.95036 |                  0.0 |            0.0 |  0.95036 |     0.54921 |           0.0 |           0.0 |            5.0 |      0.0 |    1.0 |     1.0 |  0.95036 |  1.67042 |        0.996865 |
    | 11.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |             1.682926 |               0.720061 |     0.679939 |      -0.27042 |               0.71839 |                 5.0 |             0.996865 |         0.71839 |             0.1 |           0.1 |              0.61839 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 |  0.61839 |    0.1 |     1.0 |      0.1 | 1.682926 |        0.996865 |
    | 12.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |             1.423559 |               1.582926 |          0.0 |     -0.282926 |              0.034564 |                 5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.0 |      0.1 | 1.423559 |        0.996865 |
    | 13.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |             1.285036 |               1.323559 |     0.076441 |     -0.023559 |              0.299482 |                 5.0 |             0.996865 |        0.299482 |             0.1 |           0.1 |             0.199482 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 | 0.199482 |    0.1 |     1.1 |      0.1 | 1.285036 |        0.996865 |
    | 14.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  1.3 |               1.185036 |     0.214964 |      0.114964 |              0.585979 |                 5.0 |             0.996865 |        0.585979 |             0.1 |           0.1 |             0.485979 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 | 0.485979 |    0.1 |     1.2 |      0.1 |      1.3 |        0.996865 |
    | 15.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  1.4 |                    1.2 |          0.2 |           0.1 |              0.557422 |                 5.0 |             0.996865 |        0.557422 |             0.1 |           0.1 |             0.457422 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 | 0.457422 |    0.1 |     1.3 |      0.1 |      1.4 |        0.996865 |
    | 16.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  1.5 |                    1.3 |          0.1 |           0.0 |                  0.35 |                 5.0 |             0.996865 |            0.35 |             0.1 |           0.1 |                 0.25 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 |     0.25 |    0.1 |     1.4 |      0.1 |      1.5 |        0.996865 |
    | 17.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  1.6 |                    1.4 |          0.0 |          -0.1 |              0.142578 |                 5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |             0.042578 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 | 0.042578 |    0.1 |     1.5 |      0.1 |      1.6 |        0.996865 |
    | 18.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  1.7 |                    1.5 |          0.0 |          -0.2 |              0.068641 |                 5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.6 |      0.1 |      1.7 |        0.996865 |
    | 19.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  1.8 |                    1.6 |          0.0 |          -0.3 |              0.029844 |                 5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.7 |      0.1 |      1.8 |        0.996865 |
    | 20.01. |           0.0 |         0.0 |   0.137303 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  1.9 |                    1.7 |          0.0 |          -0.4 |              0.012348 |                 5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.0 |           0.0 |            5.0 |      0.0 |    0.1 |     1.8 |      0.1 |      1.9 |        0.996865 |


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
where the available water storage is too limited for releasing enough discharge:

.. integration-test::

    >>> test("dam_v005_smooth_stage_minimum")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   demand |   inflow | natural |  outflow |   remote | required_supply |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.004292 |                   0.0 |                 0.0 |               0.0 |      0.2 |             1.800256 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |           0.005 |           0.005 |      0.001282 |             0.003718 |            0.0 | 0.001282 |    0.017169 |           0.0 |           0.0 |            5.0 | 0.003718 |      0.2 |     1.8 | 0.001282 | 1.800256 |             1.0 |
    | 02.01. |           0.0 |         0.0 |    0.00822 |                   0.0 |                 0.0 |               0.0 | 0.189474 |             1.702037 |               1.798975 |          0.0 |     -0.400256 |               0.01232 |                 5.0 |                  1.0 |         0.01232 |         0.01232 |      0.007624 |             0.004696 |            0.0 | 0.007624 |    0.032881 |           0.0 |           0.0 |            5.0 | 0.004696 | 0.189474 |     1.7 | 0.007624 | 1.702037 |             1.0 |
    | 03.01. |           0.0 |         0.0 |   0.011526 |                   0.0 |                 0.0 |               0.0 | 0.178947 |             1.608618 |               1.694414 |          0.0 |     -0.302037 |              0.029323 |                 5.0 |                  1.0 |        0.029323 |        0.029323 |      0.025921 |             0.003402 |            0.0 | 0.025921 |    0.046103 |           0.0 |           0.0 |            5.0 | 0.003402 | 0.178947 |     1.6 | 0.025921 | 1.608618 |             1.0 |
    | 04.01. |           0.0 |         0.0 |   0.013824 |                   0.0 |                 0.0 |               0.0 | 0.168421 |             1.525188 |               1.582697 |          0.0 |     -0.208618 |              0.064084 |                 5.0 |                  1.0 |        0.064084 |        0.064084 |      0.062022 |             0.002063 |            0.0 | 0.062022 |    0.055296 |           0.0 |           0.0 |            5.0 | 0.002063 | 0.168421 |     1.5 | 0.062022 | 1.525188 |             1.0 |
    | 05.01. |           0.0 |         0.0 |   0.014675 |                   0.0 |                 0.0 |               0.0 | 0.157895 |             1.457043 |               1.463166 |          0.0 |     -0.125188 |              0.120198 |                 5.0 |                  1.0 |        0.120198 |        0.120198 |      0.118479 |             0.001719 |            0.0 | 0.118479 |    0.058701 |           0.0 |           0.0 |            5.0 | 0.001719 | 0.157895 |     1.4 | 0.118479 | 1.457043 |             1.0 |
    | 06.01. |           0.0 |         0.0 |   0.012626 |                   0.0 |                 0.0 |               0.0 | 0.147368 |             1.417039 |               1.338564 |     0.061436 |     -0.057043 |              0.247367 |                 5.0 |                  1.0 |        0.247367 |        0.247367 |      0.242243 |             0.005124 |            0.0 | 0.242243 |    0.050504 |           0.0 |           0.0 |            5.0 | 0.005124 | 0.147368 |     1.3 | 0.242243 | 1.417039 |             1.0 |
    | 07.01. |           0.0 |         0.0 |   0.006999 |                   0.0 |                 0.0 |               0.0 | 0.136842 |             1.418109 |               1.174796 |     0.225204 |     -0.017039 |               0.45567 |                 5.0 |                  1.0 |         0.45567 |         0.45567 |      0.397328 |             0.058342 |            0.0 | 0.397328 |    0.027998 |           0.0 |           0.0 |            5.0 | 0.058342 | 0.136842 |     1.2 | 0.397328 | 1.418109 |             1.0 |
    | 08.01. |           0.0 |         0.0 |   0.003447 |                   0.0 |                 0.0 |               0.0 | 0.126316 |             1.401604 |               1.020781 |     0.379219 |     -0.018109 |              0.608464 |                 5.0 |                  1.0 |        0.608464 |        0.608464 |      0.290761 |             0.317702 |            0.0 | 0.290761 |     0.01379 |           0.0 |           0.0 |            5.0 | 0.317702 | 0.126316 |     1.1 | 0.290761 | 1.401604 |             1.0 |
    | 09.01. |           0.0 |         0.0 |   0.002616 |                   0.0 |                 0.0 |               0.0 | 0.115789 |             1.290584 |               1.110843 |     0.289157 |     -0.001604 |              0.537314 |                 5.0 |                  1.0 |        0.537314 |        0.537314 |      0.154283 |             0.383031 |            0.0 | 0.154283 |    0.010464 |           0.0 |           0.0 |            5.0 | 0.383031 | 0.115789 |     1.0 | 0.154283 | 1.290584 |             1.0 |
    | 10.01. |           0.0 |         0.0 |   0.001898 |                   0.0 |                 0.0 |               0.0 | 0.105263 |             1.216378 |               1.136301 |     0.263699 |      0.109416 |              0.629775 |                 5.0 |                  1.0 |        0.629775 |        0.629775 |      0.138519 |             0.491255 |            0.0 | 0.138519 |    0.007591 |           0.0 |           0.0 |            5.0 | 0.491255 | 0.105263 |     1.0 | 0.138519 | 1.216378 |             1.0 |
    | 11.01. |           0.0 |         0.0 |   0.001218 |                   0.0 |                 0.0 |               0.0 | 0.094737 |              1.15601 |               1.077859 |     0.322141 |      0.183622 |              0.744091 |                 5.0 |                  1.0 |        0.744091 |        0.744091 |      0.126207 |             0.617883 |            0.0 | 0.126207 |    0.004871 |           0.0 |           0.0 |            5.0 | 0.617883 | 0.094737 |     1.0 | 0.126207 |  1.15601 |             1.0 |
    | 12.01. |           0.0 |         0.0 |   0.000667 |                   0.0 |                 0.0 |               0.0 | 0.084211 |             1.129412 |               1.029803 |     0.370197 |       0.24399 |               0.82219 |                 5.0 |                  1.0 |         0.82219 |         0.82219 |      0.109723 |             0.712467 |            0.0 | 0.109723 |    0.002667 |           0.0 |           0.0 |            5.0 | 0.712467 | 0.084211 |     1.0 | 0.109723 | 1.129412 |             1.0 |
    | 13.01. |           0.0 |         0.0 |   0.000257 |                   0.0 |                 0.0 |               0.0 | 0.073684 |             1.214132 |               1.019689 |     0.380311 |      0.270588 |              0.841916 |                 5.0 |                  1.0 |        0.841916 |        0.841916 |      0.092645 |             0.749271 |            0.0 | 0.092645 |    0.001029 |           0.0 |           0.0 |            5.0 | 0.749271 | 0.073684 |     1.1 | 0.092645 | 1.214132 |             1.0 |
    | 14.01. |           0.0 |         0.0 |   0.000135 |                   0.0 |                 0.0 |               0.0 | 0.063158 |             1.296357 |               1.121487 |     0.278513 |      0.185868 |              0.701812 |                 5.0 |                  1.0 |        0.701812 |        0.701812 |      0.068806 |             0.633006 |            0.0 | 0.068806 |    0.000541 |           0.0 |           0.0 |            5.0 | 0.633006 | 0.063158 |     1.2 | 0.068806 | 1.296357 |             1.0 |
    | 15.01. |           0.0 |         0.0 |   0.000154 |                   0.0 |                 0.0 |               0.0 | 0.052632 |             1.376644 |               1.227551 |     0.172449 |      0.103643 |              0.533258 |                 5.0 |                  1.0 |        0.533258 |        0.533258 |      0.051779 |              0.48148 |            0.0 | 0.051779 |    0.000615 |           0.0 |           0.0 |            5.0 |  0.48148 | 0.052632 |     1.3 | 0.051779 | 1.376644 |             1.0 |
    | 16.01. |           0.0 |         0.0 |   0.000296 |                   0.0 |                 0.0 |               0.0 | 0.042105 |             1.457718 |               1.324865 |     0.075135 |      0.023356 |              0.351863 |                 5.0 |                  1.0 |        0.351863 |        0.351863 |      0.035499 |             0.316364 |            0.0 | 0.035499 |    0.001185 |           0.0 |           0.0 |            5.0 | 0.316364 | 0.042105 |     1.4 | 0.035499 | 1.457718 |             1.0 |
    | 17.01. |           0.0 |         0.0 |   0.000541 |                   0.0 |                 0.0 |               0.0 | 0.031579 |             1.540662 |               1.422218 |          0.0 |     -0.057718 |              0.185207 |                 5.0 |                  1.0 |        0.185207 |        0.185207 |       0.02024 |             0.164967 |            0.0 |  0.02024 |    0.002165 |           0.0 |           0.0 |            5.0 | 0.164967 | 0.031579 |     1.5 |  0.02024 | 1.540662 |             1.0 |
    | 18.01. |           0.0 |         0.0 |    0.00072 |                   0.0 |                 0.0 |               0.0 | 0.021053 |             1.626481 |               1.520422 |          0.0 |     -0.140662 |              0.107697 |                 5.0 |                  1.0 |        0.107697 |        0.107697 |      0.012785 |             0.094912 |            0.0 | 0.012785 |    0.002879 |           0.0 |           0.0 |            5.0 | 0.094912 | 0.021053 |     1.6 | 0.012785 | 1.626481 |             1.0 |
    | 19.01. |           0.0 |         0.0 |   0.000798 |                   0.0 |                 0.0 |               0.0 | 0.010526 |              1.71612 |               1.613695 |          0.0 |     -0.226481 |              0.055458 |                 5.0 |                  1.0 |        0.055458 |        0.055458 |      0.006918 |              0.04854 |            0.0 | 0.006918 |    0.003191 |           0.0 |           0.0 |            5.0 |  0.04854 | 0.010526 |     1.7 | 0.006918 |  1.71612 |             1.0 |
    | 20.01. |           0.0 |         0.0 |   0.000763 |                   0.0 |                 0.0 |               0.0 |      0.0 |             1.808953 |               1.709201 |          0.0 |      -0.31612 |              0.025948 |                 5.0 |                  1.0 |        0.025948 |        0.012974 |      0.001631 |             0.024317 |            0.0 | 0.001631 |     0.00305 |           0.0 |           0.0 |            5.0 | 0.024317 |      0.0 |     1.8 | 0.001631 | 1.808953 |             1.0 |

.. _dam_v005_evaporation:

evaporation
___________

This example repeats the :ref:`dam_v001_evaporation` example of application model
|dam_v001|.  We update the time series of potential evaporation accordingly:

>>> inputs.evaporation.series = 10 * [1.0] + 10 * [5.0]

All internal evaporation-related results agree with the ones of |dam_v001| exactly:

.. integration-test::

    >>> test("dam_v005_evaporation")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   demand |   inflow | natural |  outflow |   remote | required_supply |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         1.0 |   0.004034 |                   0.0 |               0.016 |             0.012 |      0.2 |             1.800247 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                 5.0 |                  1.0 |           0.005 |           0.005 |      0.001234 |             0.003766 |            0.0 | 0.001234 |    0.016137 |           0.0 |           0.0 |            5.0 | 0.003766 |      0.2 |     1.8 | 0.001234 | 1.800247 |             1.0 |
    | 02.01. |           0.0 |         1.0 |   0.007558 |                   0.0 |              0.0192 |            0.0192 | 0.189474 |             1.701922 |               1.799013 |          0.0 |     -0.400247 |              0.012321 |                 5.0 |                  1.0 |        0.012321 |        0.012321 |       0.00714 |              0.00518 |            0.0 |  0.00714 |    0.030231 |           0.0 |           0.0 |            5.0 |  0.00518 | 0.189474 |     1.7 |  0.00714 | 1.701922 |             1.0 |
    | 03.01. |           0.0 |         1.0 |   0.010459 |                   0.0 |             0.01984 |           0.01984 | 0.178947 |             1.608188 |               1.694781 |          0.0 |     -0.301922 |              0.029352 |                 5.0 |                  1.0 |        0.029352 |        0.029352 |       0.02481 |             0.004543 |            0.0 |  0.02481 |    0.041835 |           0.0 |           0.0 |            5.0 | 0.004543 | 0.178947 |     1.6 |  0.02481 | 1.608188 |             1.0 |
    | 04.01. |           0.0 |         1.0 |   0.012351 |                   0.0 |            0.019968 |          0.019968 | 0.168421 |             1.524357 |               1.583379 |          0.0 |     -0.208188 |              0.064305 |                 5.0 |                  1.0 |        0.064305 |        0.064305 |      0.060838 |             0.003467 |            0.0 | 0.060838 |    0.049405 |           0.0 |           0.0 |            5.0 | 0.003467 | 0.168421 |     1.5 | 0.060838 | 1.524357 |             1.0 |
    | 05.01. |           0.0 |         1.0 |   0.012797 |                   0.0 |            0.019994 |          0.019994 | 0.157895 |             1.455947 |               1.463519 |          0.0 |     -0.124357 |              0.120897 |                 5.0 |                  1.0 |        0.120897 |        0.120897 |      0.117273 |             0.003624 |            0.0 | 0.117273 |    0.051187 |           0.0 |           0.0 |            5.0 | 0.003624 | 0.157895 |     1.4 | 0.117273 | 1.455947 |             1.0 |
    | 06.01. |           0.0 |         1.0 |   0.010468 |                   0.0 |            0.019999 |          0.019999 | 0.147368 |             1.414679 |               1.338674 |     0.061326 |     -0.055947 |              0.248435 |                 5.0 |                  1.0 |        0.248435 |        0.248435 |      0.235187 |             0.013248 |            0.0 | 0.235187 |    0.041871 |           0.0 |           0.0 |            5.0 | 0.013248 | 0.147368 |     1.3 | 0.235187 | 1.414679 |             1.0 |
    | 07.01. |           0.0 |         1.0 |   0.005562 |                   0.0 |                0.02 |              0.02 | 0.136842 |             1.404136 |               1.179492 |     0.220508 |     -0.014679 |              0.453671 |                 5.0 |                  1.0 |        0.453671 |        0.453671 |      0.343975 |             0.109695 |            0.0 | 0.343975 |    0.022247 |           0.0 |           0.0 |            5.0 | 0.109695 | 0.136842 |     1.2 | 0.343975 | 1.404136 |             1.0 |
    | 08.01. |           0.0 |         1.0 |   0.002981 |                   0.0 |                0.02 |              0.02 | 0.126316 |              1.36503 |                1.06016 |      0.33984 |     -0.004136 |              0.585089 |                 5.0 |                  1.0 |        0.585089 |        0.585089 |      0.225783 |             0.359306 |            0.0 | 0.225783 |    0.011925 |           0.0 |           0.0 |            5.0 | 0.359306 | 0.126316 |     1.1 | 0.225783 |  1.36503 |             1.0 |
    | 09.01. |           0.0 |         1.0 |   0.002144 |                   0.0 |                0.02 |              0.02 | 0.115789 |             1.243934 |               1.139247 |     0.260753 |       0.03497 |              0.550583 |                 5.0 |                  1.0 |        0.550583 |        0.550583 |      0.134548 |             0.416035 |            0.0 | 0.134548 |    0.008576 |           0.0 |           0.0 |            5.0 | 0.416035 | 0.115789 |     1.0 | 0.134548 | 1.243934 |             1.0 |
    | 10.01. |           0.0 |         1.0 |   0.001291 |                   0.0 |                0.02 |          0.019988 | 0.105263 |             1.180908 |               1.109386 |     0.290614 |      0.156066 |              0.694398 |                 5.0 |                  1.0 |        0.694398 |        0.694398 |      0.124783 |             0.569615 |            0.0 | 0.124783 |    0.005163 |           0.0 |           0.0 |            5.0 | 0.569615 | 0.105263 |     1.0 | 0.124783 | 1.180908 |             1.0 |
    | 11.01. |           0.0 |         5.0 |   0.000063 |                   0.0 |               0.084 |          0.063974 | 0.094737 |             1.130378 |               1.056125 |     0.343875 |      0.219092 |              0.784979 |                 5.0 |                  1.0 |        0.784979 |        0.784979 |       0.08761 |             0.697369 |            0.0 |  0.08761 |    0.000251 |           0.0 |           0.0 |            5.0 | 0.697369 | 0.094737 |     1.0 |  0.08761 | 1.130378 |             1.0 |
    | 12.01. |           0.0 |         5.0 |  -0.000321 |                   0.0 |              0.0968 |          0.032045 | 0.084211 |             1.099925 |               1.042768 |     0.357232 |      0.269622 |               0.81852 |                 5.0 |                  1.0 |         0.81852 |         0.81852 |      0.069957 |             0.748564 |            0.0 | 0.069957 |   -0.001286 |           0.0 |           0.0 |            5.0 | 0.748564 | 0.084211 |     1.0 | 0.069957 | 1.099925 |             1.0 |
    | 13.01. |           0.0 |         5.0 |  -0.000374 |                   0.0 |             0.09936 |          0.012511 | 0.073684 |             1.179462 |               1.029968 |     0.370032 |      0.300075 |              0.840207 |                 5.0 |                  1.0 |        0.840207 |        0.840207 |      0.063591 |             0.776616 |            0.0 | 0.063591 |   -0.001495 |           0.0 |           0.0 |            5.0 | 0.776616 | 0.073684 |     1.1 | 0.063591 | 1.179462 |             1.0 |
    | 14.01. |           0.0 |         5.0 |  -0.000426 |                   0.0 |            0.099872 |          0.011118 | 0.063158 |              1.26608 |               1.115871 |     0.284129 |      0.220538 |               0.72592 |                 5.0 |                  1.0 |         0.72592 |         0.72592 |      0.054477 |             0.671443 |            0.0 | 0.054477 |   -0.001705 |           0.0 |           0.0 |            5.0 | 0.671443 | 0.063158 |     1.2 | 0.054477 |  1.26608 |             1.0 |
    | 15.01. |           0.0 |         5.0 |  -0.000452 |                   0.0 |            0.099974 |          0.010651 | 0.052632 |             1.356502 |               1.211603 |     0.188397 |       0.13392 |              0.575373 |                 5.0 |                  1.0 |        0.575373 |        0.575373 |      0.043191 |             0.532182 |            0.0 | 0.043191 |    -0.00181 |           0.0 |           0.0 |            5.0 | 0.532182 | 0.052632 |     1.3 | 0.043191 | 1.356502 |             1.0 |
    | 16.01. |           0.0 |         5.0 |  -0.000439 |                   0.0 |            0.099995 |          0.012092 | 0.042105 |             1.445855 |               1.313311 |     0.086689 |      0.043498 |              0.386003 |                 5.0 |                  1.0 |        0.386003 |        0.386003 |      0.029384 |             0.356619 |            0.0 | 0.029384 |   -0.001756 |           0.0 |           0.0 |            5.0 | 0.356619 | 0.042105 |     1.4 | 0.029384 | 1.445855 |             1.0 |
    | 17.01. |           0.0 |         5.0 |  -0.000406 |                   0.0 |            0.099999 |          0.014695 | 0.031579 |             1.533233 |               1.416471 |          0.0 |     -0.045855 |              0.198088 |                 5.0 |                  1.0 |        0.198088 |        0.198088 |      0.015375 |             0.182713 |            0.0 | 0.015375 |   -0.001625 |           0.0 |           0.0 |            5.0 | 0.182713 | 0.031579 |     1.5 | 0.015375 | 1.533233 |             1.0 |
    | 18.01. |           0.0 |         5.0 |  -0.000416 |                   0.0 |                 0.1 |          0.012793 | 0.021053 |             1.621024 |               1.517859 |          0.0 |     -0.133233 |              0.113577 |                 5.0 |                  1.0 |        0.113577 |        0.113577 |      0.008699 |             0.104878 |            0.0 | 0.008699 |   -0.001663 |           0.0 |           0.0 |            5.0 | 0.104878 | 0.021053 |     1.6 | 0.008699 | 1.621024 |             1.0 |
    | 19.01. |           0.0 |         5.0 |  -0.000496 |                   0.0 |                 0.1 |          0.009947 | 0.010526 |             1.711892 |               1.612325 |          0.0 |     -0.221024 |               0.05798 |                 5.0 |                  1.0 |         0.05798 |         0.05798 |       0.00431 |              0.05367 |            0.0 |  0.00431 |   -0.001985 |           0.0 |           0.0 |            5.0 |  0.05367 | 0.010526 |     1.7 |  0.00431 | 1.711892 |             1.0 |
    | 20.01. |           0.0 |         5.0 |  -0.000655 |                   0.0 |                 0.1 |          0.006415 |      0.0 |             1.806062 |               1.707582 |          0.0 |     -0.311892 |              0.026921 |                 5.0 |                  1.0 |        0.026921 |         0.01346 |      0.000952 |             0.025969 |            0.0 | 0.000952 |   -0.002622 |           0.0 |           0.0 |            5.0 | 0.025969 |      0.0 |     1.8 | 0.000952 | 1.806062 |             1.0 |

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
>>> inputs.precipitation.series = [0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inflow.sequences.sim.series = [0.0, 0.0, 5.0, 9.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inputs.evaporation.series = 0.0
>>> test.inits.loggedtotalremotedischarge = 1.0
>>> natural.sequences.sim.series = 1.0

The following test results show that |dam_v005| reproduces the water levels and outflow
values calculated by |dam_v001| precisely.  Furthermore, they illustrate the estimation
of |AllowedRemoteRelief| based on the current water level, which is functionally
similar to the one of |RequiredRemoteSupply| discussed in the
:ref:`dam_v005_smooth_near_minimum` example:

.. integration-test::

    >>> test("dam_v005_flood_retention")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelief | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | demand | inflow | natural |  outflow |   remote | required_supply |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |                 5.0 |                  1.0 |             0.0 |             0.0 |           0.0 |                  0.0 |            0.0 |      0.0 |         0.0 |           0.0 |           0.0 |            5.0 |    0.0 |    0.0 |     1.0 |      0.0 |      1.0 |             1.0 |
    | 02.01. |          50.0 |         0.0 |   0.021027 |                   1.0 |                 0.0 |               0.0 |    0.0 |             1.005303 |                    1.0 |          0.0 |          -1.0 |                   0.0 |                 5.0 |                  1.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.026514 | 0.026514 |    0.084109 |           0.0 |           0.0 |            5.0 |    0.0 |    0.0 |     1.0 | 0.026514 | 1.005303 |             1.0 |
    | 03.01. |           0.0 |         0.0 |   0.125058 |                   0.0 |                 0.0 |               0.0 |    5.0 |             1.047354 |               0.978789 |          0.0 |     -1.005303 |                   0.0 |                 5.0 |              0.99898 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.183744 | 0.183744 |    0.500234 |           0.0 |           0.0 |            5.0 |    0.0 |    5.0 |     1.0 | 0.183744 | 1.047354 |         0.99898 |
    | 04.01. |           0.0 |         0.0 |    0.30773 |                   0.0 |                 0.0 |               0.0 |    9.0 |             1.190048 |                0.86361 |          0.0 |     -1.047354 |                   0.0 |                 5.0 |              0.00005 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.542983 | 0.542983 |     1.23092 |           0.0 |           0.0 |            5.0 |    0.0 |    9.0 |     1.0 | 0.542983 | 1.190048 |         0.00005 |
    | 05.01. |           0.0 |         0.0 |   0.459772 |                   0.0 |                 0.0 |               0.0 |    8.0 |             1.467176 |               0.647066 |          0.0 |     -1.190048 |                   0.0 |            4.879022 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.961039 | 0.961039 |    1.839086 |           0.0 |           0.0 |       4.879022 |    0.0 |    8.0 |     1.0 | 0.961039 | 1.467176 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.540739 |                   0.0 |                 0.0 |               0.0 |    5.0 |             1.815989 |               0.506136 |          0.0 |     -1.467176 |                   0.0 |            0.115565 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.251523 | 1.251523 |    2.162955 |           0.0 |           0.0 |       0.115565 |    0.0 |    5.0 |     1.0 | 1.251523 | 1.815989 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.575395 |                   0.0 |                 0.0 |               0.0 |    3.0 |             2.122328 |               0.564467 |          0.0 |     -1.815989 |                   0.0 |             0.00489 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.395546 | 1.395546 |    2.301579 |           0.0 |           0.0 |        0.00489 |    0.0 |    3.0 |     1.0 | 1.395546 | 2.122328 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.587202 |                   0.0 |                 0.0 |               0.0 |    2.0 |             2.320454 |               0.726783 |          0.0 |     -2.122328 |                   0.0 |            0.001653 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.453375 | 1.453375 |    2.348808 |           0.0 |           0.0 |       0.001653 |    0.0 |    2.0 |     1.0 | 1.453375 | 2.320454 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.577361 |                   0.0 |                 0.0 |               0.0 |    1.0 |             2.416285 |               0.867079 |          0.0 |     -2.320454 |                   0.0 |            0.004082 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.455596 | 1.455596 |    2.309444 |           0.0 |           0.0 |       0.004082 |    0.0 |    1.0 |     1.0 | 1.455596 | 2.416285 |             0.0 |
    | 10.01. |           0.0 |         0.0 |    0.54701 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.438832 |               0.960689 |          0.0 |     -2.416285 |                   0.0 |            0.065604 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.405132 | 1.405132 |    2.188041 |           0.0 |           0.0 |       0.065604 |    0.0 |    0.0 |     1.0 | 1.405132 | 2.438832 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.518255 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.410323 |                 1.0337 |          0.0 |     -2.438832 |                   0.0 |            0.787024 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.331267 | 1.331267 |    2.073019 |           0.0 |           0.0 |       0.787024 |    0.0 |    0.0 |     1.0 | 1.331267 | 2.410323 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.491011 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.351863 |               1.079056 |          0.0 |     -2.410323 |                   0.0 |            3.477649 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.261285 | 1.261285 |    1.964044 |           0.0 |           0.0 |       3.477649 |    0.0 |    0.0 |     1.0 | 1.261285 | 2.351863 |             0.0 |
    | 13.01. |           0.0 |         0.0 |     0.4652 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.283403 |               1.090578 |          0.0 |     -2.351863 |                   0.0 |            4.803841 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.194981 | 1.194981 |    1.860798 |           0.0 |           0.0 |       4.803841 |    0.0 |    0.0 |     1.0 | 1.194981 | 2.283403 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.440745 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.215937 |               1.088422 |          0.0 |     -2.283403 |                   0.0 |            4.978518 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.132163 | 1.132163 |    1.762979 |           0.0 |           0.0 |       4.978518 |    0.0 |    0.0 |     1.0 | 1.132163 | 2.215937 |             0.0 |
    | 15.01. |           0.0 |         0.0 |   0.417576 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.152017 |               1.083774 |          0.0 |     -2.215937 |                   0.0 |            4.997436 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.072647 | 1.072647 |    1.670302 |           0.0 |           0.0 |       4.997436 |    0.0 |    0.0 |     1.0 | 1.072647 | 2.152017 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.395624 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.091458 |                1.07937 |          0.0 |     -2.152017 |                   0.0 |            4.999659 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |        1.01626 |  1.01626 |    1.582498 |           0.0 |           0.0 |       4.999659 |    0.0 |    0.0 |     1.0 |  1.01626 | 2.091458 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.374827 |                   0.0 |                 0.0 |               0.0 |    0.0 |             2.034082 |               1.075198 |          0.0 |     -2.091458 |                   0.0 |             4.99995 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.962837 | 0.962837 |    1.499308 |           0.0 |           0.0 |        4.99995 |    0.0 |    0.0 |     1.0 | 0.962837 | 2.034082 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.355123 |                   0.0 |                 0.0 |               0.0 |    0.0 |             1.979722 |               1.071245 |          0.0 |     -2.034082 |                   0.0 |            4.999992 |             0.000001 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.912222 | 0.912222 |    1.420492 |           0.0 |           0.0 |       4.999992 |    0.0 |    0.0 |     1.0 | 0.912222 | 1.979722 |        0.000001 |
    | 19.01. |           0.0 |         0.0 |   0.336455 |                   0.0 |                 0.0 |               0.0 |    0.0 |              1.92822 |                 1.0675 |          0.0 |     -1.979722 |                   0.0 |            4.999999 |             0.000004 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.864268 | 0.864268 |     1.34582 |           0.0 |           0.0 |       4.999999 |    0.0 |    0.0 |     1.0 | 0.864268 |  1.92822 |        0.000004 |
    | 20.01. |           0.0 |         0.0 |   0.318768 |                   0.0 |                 0.0 |               0.0 |    0.0 |             1.879425 |               1.063951 |          0.0 |      -1.92822 |                   0.0 |                 5.0 |             0.000018 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.818835 | 0.818835 |    1.275072 |           0.0 |           0.0 |            5.0 |    0.0 |    0.0 |     1.0 | 0.818835 | 1.879425 |        0.000018 |
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
    """Version 5 of HydPy-Dam."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
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
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
