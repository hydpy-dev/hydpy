# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Version 5 application model of HydPy-Dam.

Application model |dam_v005| is an extension of application model
|dam_v001|.  It provides two additional functionalities.

Just like |dam_v001|, |dam_v005| tries to increase the discharge at
a remote location in the channel downsstream during low flow conditions.
And just like |dam_v001|, |dam_v005| might sometimes fail in doing so
due to limited storage content.  One additional feature of |dam_v005| is
that it passes the information on its own failure to another remote
location.  This can e.g. enable another dam model to jump in whenever
necessary.

The second additional feature of |dam_v005| is that it receives input
from two additional nodes, one for `supply discharge` and the other one
for `relieve discharge`.  `Supply discharge` is understood as water that
is delivered from a remote location in order to increase the storage
content of |dam_v005| when necessary (during droughts). `Relieve discharge`
is understood as water that is discharged from another location in order
to relieve the other location (possibly another dam) during floods.
|dam_v005| calculates both the desirable `supply discharge` and the
acceptable `relieve discharge` and passes that information to one single
or to two seperate remote locations.

Integration examples:

    The following integration examples build upon some of the examples
    performed to demonstrate the functionality of model |dam_v001|.
    To achieve comparability, identical parameter values, initial
    conditions, and input values are set.  The following explanations
    focus on the differences between applications models |dam_v005| and
    |dam_v001| mainly.  It seems advisable to start with reading
    the documentation on application model |dam_v001|.

    The time settings are identical:

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '21.01.2000',
    ...                                    '1d'))

    Due to the high complexity of |dam_v005| and due to the test setting
    of |dam_v001| involving another type of model (|arma_v1|), lots of
    nodes are required (a picture would be helpful):

    >>> from hydpy import Node
    >>> dam_inflow = Node('actual_inflow', variable='Q')
    >>> dam_outflow = Node('dam_outflow', variable='Q')
    >>> tributary_inflow = Node('tributary_inflow', variable='Q')
    >>> tributary_mouth = Node('tributary_mouth', variable='Q')
    >>> actual_supply = Node('actual_supply', variable='S')
    >>> required_supply = Node('required_supply', variable='S')
    >>> allowed_relieve = Node('allowed_relieve', variable='R')
    >>> actual_relieve = Node('actual_relieve', variable='R')
    >>> remote_failure = Node('remote_failure', variable='D')
    >>> from hydpy import Element
    >>> dam = Element(
    ...     'dam',
    ...     inlets=(dam_inflow, actual_supply, actual_relieve),
    ...     outlets=dam_outflow,
    ...     receivers=tributary_mouth,
    ...     senders=(remote_failure, required_supply, allowed_relieve))
    >>> stream1 = Element('stream1',
    ...                    inlets=dam_outflow,
    ...                    outlets=tributary_mouth)
    >>> stream2 = Element('stream2',
    ...                   inlets=tributary_inflow,
    ...                   outlets=tributary_mouth)

    The nodes `dam_inflow` and `dam_outflow` handle the "normal" discharge
    (variable `Q`) into and out of the dam.  Node `dam_outflow` passes its
    discharge values to the routing element `stream1`.  To simulate a
    natural tributary, the second routing element `stream2` is defined,
    which receives its inflow form node `tributary_inflow`.  Both routing
    elements pass their outflow to node `tributary_mouth`. So far, this is
    the setting as the one of the examples on |dam_v001| (but with different
    names).  In addition, |dam_v005| expects two input nodes handling the
    actual supply and relieve discharge values from remote locations
    (node `actual_supply` and node `actual_relieve`) and three sender nodes
    for informing other models (which are not modelled explicitely in the
    following examples) of its required supply and allowed relieve (node
    `required_supply` and node `allowed_relieve`) and its own expected
    failure in increasing low discharge values downstream (`remote_failure`).
    Note that the defined node variable is `S` for both "supply nodes",
    `R` for both "relieve nodes" and `D` for node `remote_failure`
    (`D` stands for "demand" in this context).  These variables are of
    vital importance, as |dam_v005| needs them for realizing the specific
    funcionality of each node.

    :ref:`Recalculation of example 7 <dam_v001_ex07>`

    In the following, all settings of the |dam_v005| model and both
    |arma_v1| models that allow an exact reproduction of example 7
    of the documentation on application model |dam_v001|:

    >>> from hydpy import prepare_model
    >>> from hydpy.models import arma_v1
    >>> arma_model = prepare_model(arma_v1)
    >>> stream2.connect(arma_model)
    >>> arma_model.parameters.control.responses(((), (1.0,)))
    >>> arma_model.parameters.update()
    >>> arma_model = prepare_model(arma_v1)
    >>> stream1.connect(arma_model)
    >>> arma_model.parameters.control.responses(((), (0.2, 0.4, 0.3, 0.1)))
    >>> arma_model.parameters.update()
    >>> arma_model.sequences.logs.login = 0.0
    >>> from hydpy.models.dam_v005 import *
    >>> parameterstep('1d')
    >>> dam.connect(model)
    >>> from hydpy import IntegrationTest
    >>> IntegrationTest.plotting_options.height = 370
    >>> IntegrationTest.plotting_options.activated=(
    ...     fluxes.inflow, fluxes.outflow)
    >>> test = IntegrationTest(
    ...     dam,
    ...     inits=((states.watervolume, 0.0),
    ...            (logs.loggedtotalremotedischarge, 1.9),
    ...            (logs.loggedoutflow, 0.0),
    ...            (stream1.model.sequences.logs.login, 0.0)))
    >>> test.dateformat = '%d.%m.'
    >>> watervolume2waterlevel(
    ...         weights_input=1e-6, weights_output=1e6,
    ...         intercepts_hidden=0.0, intercepts_output=-1e6/2)
    >>> waterlevel2flooddischarge(ann(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=0.0))
    >>> catchmentarea(86.4)
    >>> nmblogentries(1)
    >>> remotedischargeminimum(1.4)
    >>> remotedischargesafety(0.5)
    >>> neardischargeminimumthreshold(0.2)
    >>> neardischargeminimumtolerance(0.2)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)
    >>> tributary_inflow.sequences.sim.series = [
    ...         1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 1.0,
    ...         1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]
    >>> dam_inflow.sequences.sim.series = 1.0/3.0
    >>> actual_supply.sequences.sim.series = 1.0/3.0
    >>> actual_relieve.sequences.sim.series = 1.0/3.0

    Note the the last three commands above, defining  the three input
    series.  In the example of |dam_v001|, the dam model receives an
    constant inflow of 1 m³/s from a single node.  In this example,
    the dam model receives the same sum of inflow via three seperate
    pathways.  This is thought to prove that all node connections are
    actually working.

    Application model |dam_v005| implements six additional control
    parameters, three for calculating the required supply and three
    for calculating the allowed relieve:

    >>> highestremotesupply(1.0)
    >>> waterlevelsupplythreshold(0.2)
    >>> waterlevelsupplytolerance(0.05)
    >>> highestremoterelieve(5.0)
    >>> waterlevelrelievethreshold(0.5)
    >>> waterlevelrelievetolerance(0.05)
    >>> parameters.update()

    First of all, the following test calculation results in the exact
    same outflow values as simulated in the corresponding integration
    example of |dam_v001|.  Secondly, the following table and figure
    contains results specific to |dam_v005|, with |RequiredRemoteRelease|
    beeing the most interesting case.  At the beginning of the simulation
    period, its value is 1 m³/s, which is the value of |HighestRemoteSupply|.
    When |WaterLevel| reaches the value of parameter
    |WaterLevelRelieveThreshold|, |RequiredRemoteRelease| decreases and
    reaches finally 0 m³/s.  Note that this decrease happens rather
    smoothly around the threshold |WaterLevel| of 0.2 m (which corresponds
    to a |WaterVolume| of 0.8 million m³), due to the smoothing parameter
    |WaterLevelSupplyTolerance| beeing set to a relatively large value:

    >>> test('dam_v005_ex7')
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelieve | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_inflow | actual_relieve | actual_supply | allowed_relieve | dam_outflow | remote_failure | required_supply | tributary_inflow | tributary_mouth |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |             1.840351 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                  5.0 |                  1.0 |        0.210526 |        0.210526 |      0.201754 |                  0.0 |            0.0 | 0.201754 |    0.068968 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.201754 |            0.0 |             1.0 |              1.8 |        1.840351 |
    | 02.01. |    1.0 |             1.822886 |               1.638597 |          0.0 |     -0.440351 |              0.008588 |                  5.0 |                  1.0 |         0.21092 |         0.21092 |       0.21092 |                  0.0 |            0.0 |  0.21092 |    0.137145 |      0.333333 |       0.333333 |      0.333333 |             5.0 |     0.21092 |            0.0 |             1.0 |              1.7 |        1.822886 |
    | 03.01. |    1.0 |             1.787111 |               1.611966 |          0.0 |     -0.422886 |              0.010053 |                  5.0 |             0.999999 |        0.211084 |        0.211084 |      0.211084 |                  0.0 |            0.0 | 0.211084 |    0.205307 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.211084 |            0.0 |        0.999999 |              1.6 |        1.787111 |
    | 04.01. |    1.0 |              1.71019 |               1.576027 |          0.0 |     -0.387111 |              0.013858 |                  5.0 |             0.999994 |        0.211523 |        0.211523 |      0.211523 |                  0.0 |            0.0 | 0.211523 |    0.273432 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.211523 |            0.0 |        0.999994 |              1.5 |         1.71019 |
    | 05.01. |    1.0 |             1.611668 |               1.498667 |          0.0 |      -0.31019 |              0.027322 |                  5.0 |             0.999973 |        0.213209 |        0.213209 |      0.213209 |                  0.0 |            0.0 | 0.213209 |     0.34141 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.213209 |            0.0 |        0.999973 |              1.4 |        1.611668 |
    | 06.01. |    1.0 |             1.513658 |               1.398459 |     0.001541 |     -0.211668 |              0.064075 |                  5.0 |             0.999875 |        0.219043 |        0.219043 |      0.219043 |                  0.0 |            0.0 | 0.219043 |    0.408885 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.219043 |            0.0 |        0.999875 |              1.3 |        1.513658 |
    | 07.01. |    1.0 |             1.429416 |               1.294615 |     0.105385 |     -0.113658 |              0.235523 |                  5.0 |             0.999481 |        0.283419 |        0.283419 |      0.283419 |                  0.0 |            0.0 | 0.283419 |    0.470798 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.283419 |            0.0 |        0.999481 |              1.2 |        1.429416 |
    | 08.01. |    1.0 |             1.395444 |               1.145997 |     0.254003 |     -0.029416 |              0.470414 |                  5.0 |             0.998531 |        0.475212 |        0.475212 |      0.475212 |                  0.0 |            0.0 | 0.475212 |    0.516139 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.475212 |            0.0 |        0.998531 |              1.1 |        1.395444 |
    | 09.01. |    1.0 |             1.444071 |               0.920232 |     0.479768 |      0.004556 |              0.735001 |                  5.0 |             0.997518 |        0.735281 |        0.735281 |      0.735281 |                  0.0 |            0.0 | 0.735281 |    0.539011 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.735281 |            0.0 |        0.997518 |              1.0 |        1.444071 |
    | 10.01. |    1.0 |             1.643281 |                0.70879 |      0.69121 |     -0.044071 |              0.891263 |                  5.0 |             0.996923 |        0.891315 |        0.891315 |      0.891315 |                  0.0 |            0.0 | 0.891315 |    0.548402 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.891315 |            0.0 |        0.996923 |              1.0 |        1.643281 |
    | 11.01. |    1.0 |             1.763981 |               0.751966 |     0.648034 |     -0.243281 |              0.696325 |                  5.0 |             0.994396 |        0.696749 |        0.696749 |      0.696749 |                  0.0 |            0.0 | 0.696749 |    0.574602 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.696749 |            0.0 |        0.994396 |              1.0 |        1.763981 |
    | 12.01. |    1.0 |             1.692903 |               1.067232 |     0.332768 |     -0.363981 |              0.349797 |                  5.0 |             0.980562 |        0.366406 |        0.366406 |      0.366406 |                  0.0 |            0.0 | 0.366406 |    0.629345 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.366406 |            0.0 |        0.980562 |              1.0 |        1.692903 |
    | 13.01. |    1.0 |             1.590367 |               1.326497 |     0.073503 |     -0.292903 |              0.105231 |                  5.0 |             0.915976 |        0.228241 |        0.228241 |      0.228241 |                  0.0 |            0.0 | 0.228241 |    0.696025 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.228241 |            0.0 |        0.915976 |              1.1 |        1.590367 |
    | 14.01. |    1.0 |             1.516904 |               1.362126 |     0.037874 |     -0.190367 |              0.111928 |                  5.0 |              0.70276 |        0.230054 |        0.230054 |      0.230054 |                  0.0 |            0.0 | 0.230054 |    0.762548 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.230054 |            0.0 |         0.70276 |              1.2 |        1.516904 |
    | 15.01. |    1.0 |             1.554409 |                1.28685 |      0.11315 |     -0.116904 |              0.240436 |                  5.0 |             0.364442 |        0.286374 |        0.286374 |      0.286374 |                  0.0 |            0.0 | 0.286374 |    0.824205 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.286374 |            0.0 |        0.364442 |              1.3 |        1.554409 |
    | 16.01. |    1.0 |             1.662351 |               1.268035 |     0.131965 |     -0.154409 |              0.229369 |                  5.0 |             0.120704 |        0.279807 |        0.279807 |      0.279807 |                  0.0 |            0.0 | 0.279807 |     0.88643 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.279807 |            0.0 |        0.120704 |              1.4 |        1.662351 |
    | 17.01. |    1.0 |             1.764451 |               1.382544 |     0.017456 |     -0.262351 |              0.058622 |                  5.0 |             0.028249 |         0.21805 |         0.21805 |       0.21805 |                  0.0 |            0.0 |  0.21805 |    0.953991 |      0.333333 |       0.333333 |      0.333333 |             5.0 |     0.21805 |            0.0 |        0.028249 |              1.5 |        1.764451 |
    | 18.01. |    1.0 |             1.842178 |                 1.5464 |          0.0 |     -0.364451 |              0.016958 |                  5.0 |             0.006045 |        0.211892 |        0.211892 |      0.211892 |                  0.0 |            0.0 | 0.211892 |    1.022083 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.211892 |            0.0 |        0.006045 |              1.6 |        1.842178 |
    | 19.01. |    1.0 |             1.920334 |               1.630286 |          0.0 |     -0.442178 |              0.008447 |                  5.0 |             0.001268 |        0.210904 |        0.210904 |      0.210904 |                  0.0 |            0.0 | 0.210904 |    1.090261 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.210904 |            0.0 |        0.001268 |              1.7 |        1.920334 |
    | 20.01. |    1.0 |             2.011822 |               1.709429 |          0.0 |     -0.520334 |              0.004155 |                  5.0 |             0.000265 |        0.210435 |        0.210435 |      0.210435 |                  0.0 |            0.0 | 0.210435 |    1.158479 |      0.333333 |       0.333333 |      0.333333 |             5.0 |    0.210435 |            0.0 |        0.000265 |              1.8 |        2.011822 |

    .. raw:: html

        <iframe
            src="dam_v005_ex7.html"
            width="100%"
            height="400px"
            frameborder=0
        ></iframe>

   :ref:`Recalculation of example 8 <dam_v001_ex08>`

    The next recalculation confirms that the restriction on releasing
    water when there is little inflow works as explained for model
    |dam_v001|.  In addition, it is shown that |MissingRemoteRelease|
    values greater than 0 m³/s result when |ActualRelease| is smaller
    than |RequiredRemoteRelease|:

    >>> dam_inflow.sequences.sim.series[:10] = 1.0
    >>> dam_inflow.sequences.sim.series[10:] = 0.1
    >>> actual_supply.sequences.sim.series = 0.0
    >>> actual_relieve.sequences.sim.series = 0.0
    >>> neardischargeminimumtolerance(0.0)
    >>> test('dam_v005_ex8')
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelieve | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_inflow | actual_relieve | actual_supply | allowed_relieve | dam_outflow | remote_failure | required_supply | tributary_inflow | tributary_mouth |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |             1.838333 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                  5.0 |                  1.0 |             0.2 |             0.2 |      0.191667 |                  0.0 |            0.0 | 0.191667 |     0.06984 |           1.0 |            0.0 |           0.0 |             5.0 |    0.191667 |            0.0 |             1.0 |              1.8 |        1.838333 |
    | 02.01. |    1.0 |             1.816667 |               1.646667 |          0.0 |     -0.438333 |              0.008746 |                  5.0 |                  1.0 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.13896 |           1.0 |            0.0 |           0.0 |             5.0 |         0.2 |            0.0 |             1.0 |              1.7 |        1.816667 |
    | 03.01. |    1.0 |               1.7775 |               1.616667 |          0.0 |     -0.416667 |              0.010632 |                  5.0 |             0.999999 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.20808 |           1.0 |            0.0 |           0.0 |             5.0 |         0.2 |            0.0 |        0.999999 |              1.6 |          1.7775 |
    | 04.01. |    1.0 |             1.699167 |                 1.5775 |          0.0 |       -0.3775 |              0.015099 |                  5.0 |             0.999994 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |      0.2772 |           1.0 |            0.0 |           0.0 |             5.0 |         0.2 |            0.0 |        0.999994 |              1.5 |        1.699167 |
    | 05.01. |    1.0 |                  1.6 |               1.499167 |          0.0 |     -0.299167 |               0.03006 |                  5.0 |              0.99997 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.34632 |           1.0 |            0.0 |           0.0 |             5.0 |         0.2 |            0.0 |         0.99997 |              1.4 |             1.6 |
    | 06.01. |    1.0 |                  1.5 |                    1.4 |          0.0 |          -0.2 |              0.068641 |                  5.0 |             0.999855 |             0.2 |             0.2 |           0.2 |                  0.0 |            0.0 |      0.2 |     0.41544 |           1.0 |            0.0 |           0.0 |             5.0 |         0.2 |            0.0 |        0.999855 |              1.3 |             1.5 |
    | 07.01. |    1.0 |             1.408516 |                    1.3 |          0.1 |          -0.1 |              0.242578 |                  5.0 |             0.999346 |        0.242578 |        0.242578 |      0.242578 |                  0.0 |            0.0 | 0.242578 |    0.480881 |           1.0 |            0.0 |           0.0 |             5.0 |    0.242578 |            0.0 |        0.999346 |              1.2 |        1.408516 |
    | 08.01. |    1.0 |             1.371888 |               1.165937 |     0.234063 |     -0.008516 |              0.474285 |                  5.0 |             0.998146 |        0.474285 |        0.474285 |      0.474285 |                  0.0 |            0.0 | 0.474285 |    0.526303 |           1.0 |            0.0 |           0.0 |             5.0 |    0.474285 |            0.0 |        0.998146 |              1.1 |        1.371888 |
    | 09.01. |    1.0 |              1.43939 |               0.897603 |     0.502397 |      0.028112 |              0.784512 |                  5.0 |             0.997159 |        0.784512 |        0.784512 |      0.784512 |                  0.0 |            0.0 | 0.784512 |    0.544921 |           1.0 |            0.0 |           0.0 |             5.0 |    0.784512 |            0.0 |        0.997159 |              1.0 |         1.43939 |
    | 10.01. |    1.0 |              1.67042 |               0.654878 |     0.745122 |      -0.03939 |               0.95036 |                  5.0 |             0.996865 |         0.95036 |         0.95036 |       0.95036 |                  0.0 |            0.0 |  0.95036 |     0.54921 |           1.0 |            0.0 |           0.0 |             5.0 |     0.95036 |            0.0 |        0.996865 |              1.0 |         1.67042 |
    | 11.01. |    0.1 |             1.682926 |               0.720061 |     0.679939 |      -0.27042 |               0.71839 |                  5.0 |             0.996865 |         0.71839 |             0.1 |           0.1 |              0.61839 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |        0.61839 |        0.996865 |              1.0 |        1.682926 |
    | 12.01. |    0.1 |             1.423559 |               1.582926 |          0.0 |     -0.282926 |              0.034564 |                  5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |            0.0 |        0.996865 |              1.0 |        1.423559 |
    | 13.01. |    0.1 |             1.285036 |               1.323559 |     0.076441 |     -0.023559 |              0.299482 |                  5.0 |             0.996865 |        0.299482 |             0.1 |           0.1 |             0.199482 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |       0.199482 |        0.996865 |              1.1 |        1.285036 |
    | 14.01. |    0.1 |                  1.3 |               1.185036 |     0.214964 |      0.114964 |              0.585979 |                  5.0 |             0.996865 |        0.585979 |             0.1 |           0.1 |             0.485979 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |       0.485979 |        0.996865 |              1.2 |             1.3 |
    | 15.01. |    0.1 |                  1.4 |                    1.2 |          0.2 |           0.1 |              0.557422 |                  5.0 |             0.996865 |        0.557422 |             0.1 |           0.1 |             0.457422 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |       0.457422 |        0.996865 |              1.3 |             1.4 |
    | 16.01. |    0.1 |                  1.5 |                    1.3 |          0.1 |          -0.0 |                  0.35 |                  5.0 |             0.996865 |            0.35 |             0.1 |           0.1 |                 0.25 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |           0.25 |        0.996865 |              1.4 |             1.5 |
    | 17.01. |    0.1 |                  1.6 |                    1.4 |          0.0 |          -0.1 |              0.142578 |                  5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |             0.042578 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |       0.042578 |        0.996865 |              1.5 |             1.6 |
    | 18.01. |    0.1 |                  1.7 |                    1.5 |          0.0 |          -0.2 |              0.068641 |                  5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |            0.0 |        0.996865 |              1.6 |             1.7 |
    | 19.01. |    0.1 |                  1.8 |                    1.6 |          0.0 |          -0.3 |              0.029844 |                  5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |            0.0 |        0.996865 |              1.7 |             1.8 |
    | 20.01. |    0.1 |                  1.9 |                    1.7 |          0.0 |          -0.4 |              0.012348 |                  5.0 |             0.996865 |             0.2 |             0.1 |           0.1 |                  0.0 |            0.0 |      0.1 |     0.54921 |           0.1 |            0.0 |           0.0 |             5.0 |         0.1 |            0.0 |        0.996865 |              1.8 |             1.9 |

    .. raw:: html

        <iframe
            src="dam_v005_ex8.html"
            width="100%"
            height="400px"
            frameborder=0
        ></iframe>

    :ref:`Recalculation of example 10 <dam_v001_ex10>`

    The last recalculation for low flow conditions deals with a case where
    the available water storage is too limited to supply enough discharge.
    Again, there is perfect agreement with the corresponding results
    of |dam_v001|:

    >>> waterlevelminimumtolerance(0.01)
    >>> waterlevelminimumthreshold(0.005)
    >>> dam_inflow.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)
    >>> test('dam_v005_ex10')
    |   date |   inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelieve | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_inflow | actual_relieve | actual_supply | allowed_relieve | dam_outflow | remote_failure | required_supply | tributary_inflow | tributary_mouth |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |      0.2 |             1.807702 |                    1.9 |          0.0 |          -0.5 |                 0.005 |                  5.0 |                  1.0 |             0.2 |             0.2 |      0.038512 |                  0.0 |            0.0 | 0.038512 |    0.013953 |           0.2 |            0.0 |           0.0 |             5.0 |    0.038512 |            0.0 |             1.0 |              1.8 |        1.807702 |
    | 02.01. | 0.189474 |             1.732852 |                1.76919 |          0.0 |     -0.407702 |              0.011524 |                  5.0 |                  1.0 |             0.2 |        0.189474 |      0.087238 |                  0.0 |            0.0 | 0.087238 |    0.022786 |      0.189474 |            0.0 |           0.0 |             5.0 |    0.087238 |            0.0 |             1.0 |              1.7 |        1.732852 |
    | 03.01. | 0.178947 |             1.669885 |               1.645614 |          0.0 |     -0.332852 |              0.022415 |                  5.0 |                  1.0 |             0.2 |        0.178947 |      0.117178 |                  0.0 |            0.0 | 0.117178 |    0.028123 |      0.178947 |            0.0 |           0.0 |             5.0 |    0.117178 |            0.0 |             1.0 |              1.6 |        1.669885 |
    | 04.01. | 0.168421 |             1.602505 |               1.552706 |          0.0 |     -0.269885 |              0.038625 |                  5.0 |                  1.0 |             0.2 |        0.168421 |      0.128057 |                  0.0 |            0.0 | 0.128057 |     0.03161 |      0.168421 |            0.0 |           0.0 |             5.0 |    0.128057 |            0.0 |             1.0 |              1.5 |        1.602505 |
    | 05.01. | 0.157895 |             1.520865 |               1.474448 |          0.0 |     -0.202505 |              0.067289 |                  5.0 |                  1.0 |             0.2 |        0.157895 |      0.128824 |                  0.0 |            0.0 | 0.128824 |    0.034122 |      0.157895 |            0.0 |           0.0 |             5.0 |    0.128824 |            0.0 |             1.0 |              1.4 |        1.520865 |
    | 06.01. | 0.147368 |             1.426729 |               1.392041 |     0.007959 |     -0.120865 |              0.131822 |                  5.0 |                  1.0 |             0.2 |        0.147368 |      0.125323 |             0.006499 |            0.0 | 0.125323 |    0.036026 |      0.147368 |            0.0 |           0.0 |             5.0 |    0.125323 |       0.006499 |             1.0 |              1.3 |        1.426729 |
    | 07.01. | 0.136842 |             1.325484 |               1.301406 |     0.098594 |     -0.026729 |              0.318041 |                  5.0 |                  1.0 |        0.318041 |        0.136842 |       0.11951 |             0.198531 |            0.0 |  0.11951 |    0.037524 |      0.136842 |            0.0 |           0.0 |             5.0 |     0.11951 |       0.198531 |             1.0 |              1.2 |        1.325484 |
    | 08.01. | 0.126316 |             1.220753 |               1.205974 |     0.194026 |      0.074516 |              0.526433 |                  5.0 |                  1.0 |        0.526433 |        0.126316 |      0.112348 |             0.414085 |            0.0 | 0.112348 |    0.038731 |      0.126316 |            0.0 |           0.0 |             5.0 |    0.112348 |       0.414085 |             1.0 |              1.1 |        1.220753 |
    | 09.01. | 0.115789 |             1.114193 |               1.108405 |     0.291595 |      0.179247 |               0.71086 |                  5.0 |                  1.0 |         0.71086 |        0.115789 |      0.104345 |             0.606515 |            0.0 | 0.104345 |     0.03972 |      0.115789 |            0.0 |           0.0 |             5.0 |    0.104345 |       0.606515 |             1.0 |              1.0 |        1.114193 |
    | 10.01. | 0.105263 |             1.106551 |               1.009849 |     0.390151 |      0.285807 |              0.856429 |                  5.0 |                  1.0 |        0.856429 |        0.105263 |      0.095788 |             0.760641 |            0.0 | 0.095788 |    0.040538 |      0.105263 |            0.0 |           0.0 |             5.0 |    0.095788 |       0.760641 |             1.0 |              1.0 |        1.106551 |
    | 11.01. | 0.094737 |             1.098224 |               1.010763 |     0.389237 |      0.293449 |              0.857658 |                  5.0 |                  1.0 |        0.857658 |        0.094737 |      0.086852 |             0.770806 |            0.0 | 0.086852 |    0.041219 |      0.094737 |            0.0 |           0.0 |             5.0 |    0.086852 |       0.770806 |             1.0 |              1.0 |        1.098224 |
    | 12.01. | 0.084211 |             1.089441 |               1.011372 |     0.388628 |      0.301776 |              0.859239 |                  5.0 |                  1.0 |        0.859239 |        0.084211 |      0.077648 |             0.781591 |            0.0 | 0.077648 |    0.041786 |      0.084211 |            0.0 |           0.0 |             5.0 |    0.077648 |       0.781591 |             1.0 |              1.0 |        1.089441 |
    | 13.01. | 0.073684 |             1.180343 |               1.011794 |     0.388206 |      0.310559 |              0.860972 |                  5.0 |                  1.0 |        0.860972 |        0.073684 |      0.068248 |             0.792723 |            0.0 | 0.068248 |    0.042256 |      0.073684 |            0.0 |           0.0 |             5.0 |    0.068248 |       0.792723 |             1.0 |              1.1 |        1.180343 |
    | 14.01. | 0.063158 |              1.27102 |               1.112095 |     0.287905 |      0.219657 |              0.729278 |                  5.0 |                  1.0 |        0.729278 |        0.063158 |      0.058705 |             0.670573 |            0.0 | 0.058705 |    0.042641 |      0.063158 |            0.0 |           0.0 |             5.0 |    0.058705 |       0.670573 |             1.0 |              1.2 |         1.27102 |
    | 15.01. | 0.052632 |             1.361533 |               1.212314 |     0.187686 |       0.12898 |               0.57064 |                  5.0 |                  1.0 |         0.57064 |        0.052632 |      0.049056 |             0.521584 |            0.0 | 0.049056 |     0.04295 |      0.052632 |            0.0 |           0.0 |             5.0 |    0.049056 |       0.521584 |             1.0 |              1.3 |        1.361533 |
    | 16.01. | 0.042105 |             1.451924 |               1.312477 |     0.087523 |      0.038467 |              0.381259 |                  5.0 |                  1.0 |        0.381259 |        0.042105 |      0.039328 |             0.341932 |            0.0 | 0.039328 |     0.04319 |      0.042105 |            0.0 |           0.0 |             5.0 |    0.039328 |       0.341932 |             1.0 |              1.4 |        1.451924 |
    | 17.01. | 0.031579 |             1.542227 |               1.412597 |          0.0 |     -0.051924 |              0.191457 |                  5.0 |                  1.0 |             0.2 |        0.031579 |      0.029542 |             0.161915 |            0.0 | 0.029542 |    0.043366 |      0.031579 |            0.0 |           0.0 |             5.0 |    0.029542 |       0.161915 |             1.0 |              1.5 |        1.542227 |
    | 18.01. | 0.021053 |             1.632464 |               1.512685 |          0.0 |     -0.142227 |              0.106486 |                  5.0 |                  1.0 |             0.2 |        0.021053 |      0.019715 |             0.086771 |            0.0 | 0.019715 |    0.043481 |      0.021053 |            0.0 |           0.0 |             5.0 |    0.019715 |       0.086771 |             1.0 |              1.6 |        1.632464 |
    | 19.01. | 0.010526 |             1.722654 |               1.612748 |          0.0 |     -0.232464 |              0.052805 |                  5.0 |                  1.0 |             0.2 |        0.010526 |      0.009864 |             0.042941 |            0.0 | 0.009864 |    0.043539 |      0.010526 |            0.0 |           0.0 |             5.0 |    0.009864 |       0.042941 |             1.0 |              1.7 |        1.722654 |
    | 20.01. |      0.0 |             1.812814 |                1.71279 |          0.0 |     -0.322654 |               0.02451 |                  5.0 |                  1.0 |             0.2 |             0.0 |           0.0 |              0.02451 |            0.0 |      0.0 |    0.043539 |           0.0 |            0.0 |           0.0 |             5.0 |         0.0 |        0.02451 |             1.0 |              1.8 |        1.812814 |

    .. raw:: html

        <iframe
            src="dam_v005_ex10.html"
            width="100%"
            height="400px"
            frameborder=0
        ></iframe>

    :ref:`Recalculation of example 13 <dam_v001_ex13>`

    The final recalculation shows the equality of both application
    models |dam_v001| and |dam_v005| under high flow conditions.
    This example also demonstrates the determination of
    |AllowedRemoteRelieve|, which is functionally similar to the
    determination of |RequiredRemoteSupply| discussed above:

    >>> remotedischargeminimum(0.0)
    >>> remotedischargesafety(0.0)
    >>> neardischargeminimumthreshold(0.0)
    >>> neardischargeminimumtolerance(0.0)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)
    >>> waterlevel2flooddischarge(ann(
    ...         weights_input=1e-6, weights_output=1e7,
    ...         intercepts_hidden=0.0, intercepts_output=-1e7/2))
    >>> neardischargeminimumthreshold(0.0)
    >>> dam_inflow.sequences.sim.series = [
    ...     0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...     0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    >>> test.inits.loggedtotalremotedischarge = 1.0
    >>> tributary_inflow.sequences.sim.series = 1.0

    >>> test('dam_v005_ex13')
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | allowedremoterelieve | requiredremotesupply | requiredrelease | targetedrelease | actualrelease | missingremoterelease | flooddischarge |  outflow | watervolume | actual_inflow | actual_relieve | actual_supply | allowed_relieve | dam_outflow | remote_failure | required_supply | tributary_inflow | tributary_mouth |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |                  5.0 |                  1.0 |             0.0 |             0.0 |           0.0 |                  0.0 |            0.0 |      0.0 |         0.0 |           0.0 |            0.0 |           0.0 |             5.0 |         0.0 |            0.0 |             1.0 |              1.0 |             1.0 |
    | 02.01. |    1.0 |             1.005303 |                    1.0 |          0.0 |          -1.0 |                   0.0 |                  5.0 |                  1.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.026514 | 0.026514 |    0.084109 |           1.0 |            0.0 |           0.0 |             5.0 |    0.026514 |            0.0 |             1.0 |              1.0 |        1.005303 |
    | 03.01. |    5.0 |             1.047354 |               0.978789 |          0.0 |     -1.005303 |                   0.0 |                  5.0 |             0.998985 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.183744 | 0.183744 |    0.500234 |           5.0 |            0.0 |           0.0 |             5.0 |    0.183744 |            0.0 |        0.998985 |              1.0 |        1.047354 |
    | 04.01. |    9.0 |             1.190048 |                0.86361 |          0.0 |     -1.047354 |                   0.0 |                  5.0 |             0.000051 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.542983 | 0.542983 |     1.23092 |           9.0 |            0.0 |           0.0 |             5.0 |    0.542983 |            0.0 |        0.000051 |              1.0 |        1.190048 |
    | 05.01. |    8.0 |             1.467176 |               0.647066 |          0.0 |     -1.190048 |                   0.0 |             4.879843 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.961039 | 0.961039 |    1.839086 |           8.0 |            0.0 |           0.0 |        4.879843 |    0.961039 |            0.0 |             0.0 |              1.0 |        1.467176 |
    | 06.01. |    5.0 |             1.815989 |               0.506136 |          0.0 |     -1.467176 |                   0.0 |             0.115985 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.251523 | 1.251523 |    2.162955 |           5.0 |            0.0 |           0.0 |        0.115985 |    1.251523 |            0.0 |             0.0 |              1.0 |        1.815989 |
    | 07.01. |    3.0 |             2.122328 |               0.564467 |          0.0 |     -1.815989 |                   0.0 |             0.004898 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.395546 | 1.395546 |    2.301579 |           3.0 |            0.0 |           0.0 |        0.004898 |    1.395546 |            0.0 |             0.0 |              1.0 |        2.122328 |
    | 08.01. |    2.0 |             2.320454 |               0.726783 |          0.0 |     -2.122328 |                   0.0 |             0.001654 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.453375 | 1.453375 |    2.348808 |           2.0 |            0.0 |           0.0 |        0.001654 |    1.453375 |            0.0 |             0.0 |              1.0 |        2.320454 |
    | 09.01. |    1.0 |             2.416285 |               0.867079 |          0.0 |     -2.320454 |                   0.0 |             0.004081 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.455596 | 1.455596 |    2.309444 |           1.0 |            0.0 |           0.0 |        0.004081 |    1.455596 |            0.0 |             0.0 |              1.0 |        2.416285 |
    | 10.01. |    0.0 |             2.438832 |               0.960689 |          0.0 |     -2.416285 |                   0.0 |             0.065514 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.405132 | 1.405132 |    2.188041 |           0.0 |            0.0 |           0.0 |        0.065514 |    1.405132 |            0.0 |             0.0 |              1.0 |        2.438832 |
    | 11.01. |    0.0 |             2.410323 |                 1.0337 |          0.0 |     -2.438832 |                   0.0 |              0.78615 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.331267 | 1.331267 |    2.073019 |           0.0 |            0.0 |           0.0 |         0.78615 |    1.331267 |            0.0 |             0.0 |              1.0 |        2.410323 |
    | 12.01. |    0.0 |             2.351863 |               1.079056 |          0.0 |     -2.410323 |                   0.0 |             3.476325 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.261285 | 1.261285 |    1.964044 |           0.0 |            0.0 |           0.0 |        3.476325 |    1.261285 |            0.0 |             0.0 |              1.0 |        2.351863 |
    | 13.01. |    0.0 |             2.283403 |               1.090578 |          0.0 |     -2.351863 |                   0.0 |             4.803618 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.194981 | 1.194981 |    1.860798 |           0.0 |            0.0 |           0.0 |        4.803618 |    1.194981 |            0.0 |             0.0 |              1.0 |        2.283403 |
    | 14.01. |    0.0 |             2.215937 |               1.088422 |          0.0 |     -2.283403 |                   0.0 |             4.978494 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.132163 | 1.132163 |    1.762979 |           0.0 |            0.0 |           0.0 |        4.978494 |    1.132163 |            0.0 |             0.0 |              1.0 |        2.215937 |
    | 15.01. |    0.0 |             2.152017 |               1.083774 |          0.0 |     -2.215937 |                   0.0 |             4.997433 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       1.072647 | 1.072647 |    1.670302 |           0.0 |            0.0 |           0.0 |        4.997433 |    1.072647 |            0.0 |             0.0 |              1.0 |        2.152017 |
    | 16.01. |    0.0 |             2.091458 |                1.07937 |          0.0 |     -2.152017 |                   0.0 |             4.999658 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |        1.01626 |  1.01626 |    1.582498 |           0.0 |            0.0 |           0.0 |        4.999658 |     1.01626 |            0.0 |             0.0 |              1.0 |        2.091458 |
    | 17.01. |    0.0 |             2.034082 |               1.075198 |          0.0 |     -2.091458 |                   0.0 |             4.999949 |                  0.0 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.962837 | 0.962837 |    1.499308 |           0.0 |            0.0 |           0.0 |        4.999949 |    0.962837 |            0.0 |             0.0 |              1.0 |        2.034082 |
    | 18.01. |    0.0 |             1.979722 |               1.071245 |          0.0 |     -2.034082 |                   0.0 |             4.999992 |             0.000001 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.912222 | 0.912222 |    1.420492 |           0.0 |            0.0 |           0.0 |        4.999992 |    0.912222 |            0.0 |        0.000001 |              1.0 |        1.979722 |
    | 19.01. |    0.0 |              1.92822 |                 1.0675 |          0.0 |     -1.979722 |                   0.0 |             4.999999 |             0.000004 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.864268 | 0.864268 |     1.34582 |           0.0 |            0.0 |           0.0 |        4.999999 |    0.864268 |            0.0 |        0.000004 |              1.0 |         1.92822 |
    | 20.01. |    0.0 |             1.879425 |               1.063951 |          0.0 |      -1.92822 |                   0.0 |                  5.0 |             0.000018 |             0.0 |             0.0 |           0.0 |                  0.0 |       0.818835 | 0.818835 |    1.275072 |           0.0 |            0.0 |           0.0 |             5.0 |    0.818835 |            0.0 |        0.000018 |              1.0 |        1.879425 |

    .. raw:: html

        <iframe
            src="dam_v005_ex13.html"
            width="100%"
            height="400px"
            frameborder=0
        ></iframe>
"""
# import...
# ...from standard library
from __future__ import division, print_function
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from HydPy
from hydpy.core.modelimports import *
from hydpy.auxs.anntools import ann
# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_control
from hydpy.models.dam import dam_derived
from hydpy.models.dam import dam_solver
from hydpy.models.dam import dam_fluxes
from hydpy.models.dam import dam_states
from hydpy.models.dam import dam_logs
from hydpy.models.dam import dam_aides
from hydpy.models.dam import dam_inlets
from hydpy.models.dam import dam_outlets
from hydpy.models.dam import dam_receivers
from hydpy.models.dam import dam_senders


class Model(modeltools.ModelELS):
    """Version 5 of HydPy-Dam."""

    _INLET_METHODS = (dam_model.pic_inflow_v2,
                      dam_model.calc_naturalremotedischarge_v1,
                      dam_model.calc_remotedemand_v1,
                      dam_model.calc_remotefailure_v1,
                      dam_model.calc_requiredremoterelease_v1,
                      dam_model.calc_requiredrelease_v1,
                      dam_model.calc_targetedrelease_v1)
    _RECEIVER_METHODS = (dam_model.pic_totalremotedischarge_v1,
                         dam_model.update_loggedtotalremotedischarge_v1)
    _PART_ODE_METHODS = (dam_model.pic_inflow_v2,
                         dam_model.calc_waterlevel_v1,
                         dam_model.calc_actualrelease_v1,
                         dam_model.calc_flooddischarge_v1,
                         dam_model.calc_outflow_v1)
    _FULL_ODE_METHODS = (dam_model.update_watervolume_v1,)
    _OUTLET_METHODS = (dam_model.pass_outflow_v1,
                       dam_model.update_loggedoutflow_v1)
    _SENDER_METHODS = (dam_model.calc_missingremoterelease_v1,
                       dam_model.pass_missingremoterelease_v1,
                       dam_model.calc_allowedremoterelieve_v2,
                       dam_model.pass_allowedremoterelieve_v1,
                       dam_model.calc_requiredremotesupply_v1,
                       dam_model.pass_requiredremotesupply_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-Dam, Version 5."""
    _PARCLASSES = (dam_control.CatchmentArea,
                   dam_control.NmbLogEntries,
                   dam_control.RemoteDischargeMinimum,
                   dam_control.RemoteDischargeSafety,
                   dam_control.NearDischargeMinimumThreshold,
                   dam_control.NearDischargeMinimumTolerance,
                   dam_control.WaterLevelMinimumThreshold,
                   dam_control.WaterLevelMinimumTolerance,
                   dam_control.HighestRemoteRelieve,
                   dam_control.WaterLevelRelieveThreshold,
                   dam_control.WaterLevelRelieveTolerance,
                   dam_control.HighestRemoteSupply,
                   dam_control.WaterLevelSupplyThreshold,
                   dam_control.WaterLevelSupplyTolerance,
                   dam_control.WaterVolume2WaterLevel,
                   dam_control.WaterLevel2FloodDischarge)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-Dam, Version 5."""
    _PARCLASSES = (dam_derived.TOY,
                   dam_derived.Seconds,
                   dam_derived.RemoteDischargeSmoothPar,
                   dam_derived.NearDischargeMinimumSmoothPar1,
                   dam_derived.NearDischargeMinimumSmoothPar2,
                   dam_derived.WaterLevelMinimumSmoothPar,
                   dam_derived.WaterLevelRelieveSmoothPar,
                   dam_derived.WaterLevelSupplySmoothPar)


class SolverParameters(parametertools.SubParameters):
    """Solver parameters of HydPy-Dam, Version 5."""
    _PARCLASSES = (dam_solver.AbsErrorMax,
                   dam_solver.RelDTMin)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_fluxes.Inflow,
                   dam_fluxes.TotalRemoteDischarge,
                   dam_fluxes.NaturalRemoteDischarge,
                   dam_fluxes.RemoteDemand,
                   dam_fluxes.RemoteFailure,
                   dam_fluxes.RequiredRemoteRelease,
                   dam_fluxes.AllowedRemoteRelieve,
                   dam_fluxes.RequiredRemoteSupply,
                   dam_fluxes.RequiredRelease,
                   dam_fluxes.TargetedRelease,
                   dam_fluxes.ActualRelease,
                   dam_fluxes.MissingRemoteRelease,
                   dam_fluxes.FloodDischarge,
                   dam_fluxes.Outflow)


class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_states.WaterVolume,)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_logs.LoggedTotalRemoteDischarge,
                   dam_logs.LoggedOutflow)


class AideSequences(sequencetools.AideSequences):
    """State sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_aides.WaterLevel,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_inlets.Q,
                   dam_inlets.S,
                   dam_inlets.R)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_outlets.Q,)


class ReceiverSequences(sequencetools.LinkSequences):
    """Information link sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_receivers.Q,)


class SenderSequences(sequencetools.LinkSequences):
    """Information link sequences of HydPy-Dam, Version 5."""
    _SEQCLASSES = (dam_senders.D,
                   dam_senders.S,
                   dam_senders.R)


autodoc_applicationmodel()

# pylint: disable=invalid-name
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
