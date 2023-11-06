# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Version 3 of HydPy-Dam.

|dam_v000| is the base version of dam_v001 - dam_v005.
|dam_v000| is supposed to represent a dam with a "passive" high water control scheme.

During low flow conditions, |dam_v000| tries to increase low runoff values immediately
downstream the dam according to the neardischargeminimum.

During high flow conditions, |dam_v001| is controlled by two relationships: one
between water volume and water level, the other one between discharge and water level.
While the first one is stationary, the second one can vary seasonally.  In both cases,
one defines these relationships via interpolators.  See the documentation on the
classes |PPoly| and |ANN|, which explains how to configure stepwise linear, spline, or
neural network-based interpolations.

|dam_v000| solves its differential equation with an adaptive Runge-Kutta method that
only works well on continuous equations.  Hence, we defined most threshold-based
low-flow equations in a "smoothable" manner.  However, defining realistic and
computationally efficient configurations of the related smoothing parameters requires
some experience.  Therefore, it seems advisable to investigate the functioning of each
new model parameterisation on several synthetic or measured drought events.


and selected an artificial neural network
for specifying the relationship between discharge and water level.


The applied solver is an explicit Runge-Kutta method that is not best-suited for stiff
initial value problems.  Its adaptive order and stepsize control prevent inaccurate
results caused by stability issues.  But for very responsive dams, increased
computations times are possible.  We come back to this point at the end of this section.

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
>>> dam = Element("dam",
...               inlets=inflow,
...               outlets=outflow)
>>> from hydpy.models.dam_v000 import *
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
...             (logs.loggedadjustedevaporation, 0.0))

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
>>> restricttargetedrelease(False)
>>> surfacearea(1.44)
>>> correctionprecipitation(1.2)
>>> correctionevaporation(1.2)
>>> weightevaporation(0.8)
>>> thresholdevaporation(0.0)
>>> toleranceevaporation(0.001)

low flow
___________________

>>> inflow.sequences.sim.series[10:] = 0.1

:

.. integration-test::

    >>> test("dam_v003_low_flow")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |    0.01746 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |      0.191667 |            0.0 | 0.191667 |     0.06984 |    1.0 | 0.191667 |
    | 02.01. |           0.0 |         0.0 |    0.03474 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.13896 |    1.0 |      0.2 |
    | 03.01. |           0.0 |         0.0 |    0.05202 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.20808 |    1.0 |      0.2 |
    | 04.01. |           0.0 |         0.0 |     0.0693 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      0.2772 |    1.0 |      0.2 |
    | 05.01. |           0.0 |         0.0 |    0.08658 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.34632 |    1.0 |      0.2 |
    | 06.01. |           0.0 |         0.0 |    0.10386 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.41544 |    1.0 |      0.2 |
    | 07.01. |           0.0 |         0.0 |    0.12114 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.48456 |    1.0 |      0.2 |
    | 08.01. |           0.0 |         0.0 |    0.13842 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.55368 |    1.0 |      0.2 |
    | 09.01. |           0.0 |         0.0 |     0.1557 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      0.6228 |    1.0 |      0.2 |
    | 10.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.69192 |    1.0 |      0.2 |
    | 11.01. |           0.0 |         0.0 |    0.17082 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.68328 |    0.1 |      0.2 |
    | 12.01. |           0.0 |         0.0 |    0.16866 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.67464 |    0.1 |      0.2 |
    | 13.01. |           0.0 |         0.0 |     0.1665 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |       0.666 |    0.1 |      0.2 |
    | 14.01. |           0.0 |         0.0 |    0.16434 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.65736 |    0.1 |      0.2 |
    | 15.01. |           0.0 |         0.0 |    0.16218 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.64872 |    0.1 |      0.2 |
    | 16.01. |           0.0 |         0.0 |    0.16002 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.64008 |    0.1 |      0.2 |
    | 17.01. |           0.0 |         0.0 |    0.15786 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.63144 |    0.1 |      0.2 |
    | 18.01. |           0.0 |         0.0 |     0.1557 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      0.6228 |    0.1 |      0.2 |
    | 19.01. |           0.0 |         0.0 |    0.15354 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.61416 |    0.1 |      0.2 |
    | 20.01. |           0.0 |         0.0 |    0.15138 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.60552 |    0.1 |      0.2 |


restriction enabled
___________________

This example corresponds to the :ref:`dam_v001_restriction_enabled` example of
application model |dam_v001| and the :ref:`dam_v002_restriction_enabled` example of
application model |dam_v002|.  We update the time series of the inflow and the required
remote release accordingly:

>>> inflow.sequences.sim.series[10:] = 0.1
>>> restricttargetedrelease(True)
>>> neardischargeminimumtolerance(0.0)

The results show that the restriction on releasing water during low inflow conditions
concerns the release into the channel downstream only:

.. integration-test::

    >>> test("dam_v003_restriction_enabled")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |    0.01746 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |      0.191667 |            0.0 | 0.191667 |     0.06984 |    1.0 | 0.191667 |
    | 02.01. |           0.0 |         0.0 |    0.03474 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.13896 |    1.0 |      0.2 |
    | 03.01. |           0.0 |         0.0 |    0.05202 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.20808 |    1.0 |      0.2 |
    | 04.01. |           0.0 |         0.0 |     0.0693 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      0.2772 |    1.0 |      0.2 |
    | 05.01. |           0.0 |         0.0 |    0.08658 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.34632 |    1.0 |      0.2 |
    | 06.01. |           0.0 |         0.0 |    0.10386 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.41544 |    1.0 |      0.2 |
    | 07.01. |           0.0 |         0.0 |    0.12114 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.48456 |    1.0 |      0.2 |
    | 08.01. |           0.0 |         0.0 |    0.13842 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.55368 |    1.0 |      0.2 |
    | 09.01. |           0.0 |         0.0 |     0.1557 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      0.6228 |    1.0 |      0.2 |
    | 10.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.69192 |    1.0 |      0.2 |
    | 11.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 12.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 13.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 14.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 15.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 16.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 17.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 18.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 19.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |
    | 20.01. |           0.0 |         0.0 |    0.17298 |                   0.0 |                 0.0 |               0.0 |    0.1 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.69192 |    0.1 |      0.1 |

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
>>> neardischargeminimumthreshold
neardischargeminimumthreshold(0.2)

.. integration-test::

    >>> test("dam_v003_smooth_stage_minimum")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume |   inflow |  outflow |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.003488 |                   0.0 |                 0.0 |               0.0 |      0.2 |             0.2 |             0.2 |      0.038512 |            0.0 | 0.038512 |    0.013953 |      0.2 | 0.038512 |
    | 02.01. |           0.0 |         0.0 |   0.005696 |                   0.0 |                 0.0 |               0.0 | 0.189474 |             0.2 |        0.189474 |      0.087238 |            0.0 | 0.087238 |    0.022786 | 0.189474 | 0.087238 |
    | 03.01. |           0.0 |         0.0 |   0.007031 |                   0.0 |                 0.0 |               0.0 | 0.178947 |             0.2 |        0.178947 |      0.117178 |            0.0 | 0.117178 |    0.028123 | 0.178947 | 0.117178 |
    | 04.01. |           0.0 |         0.0 |   0.007902 |                   0.0 |                 0.0 |               0.0 | 0.168421 |             0.2 |        0.168421 |      0.128057 |            0.0 | 0.128057 |     0.03161 | 0.168421 | 0.128057 |
    | 05.01. |           0.0 |         0.0 |    0.00853 |                   0.0 |                 0.0 |               0.0 | 0.157895 |             0.2 |        0.157895 |      0.128824 |            0.0 | 0.128824 |    0.034122 | 0.157895 | 0.128824 |
    | 06.01. |           0.0 |         0.0 |   0.009007 |                   0.0 |                 0.0 |               0.0 | 0.147368 |             0.2 |        0.147368 |      0.125323 |            0.0 | 0.125323 |    0.036026 | 0.147368 | 0.125323 |
    | 07.01. |           0.0 |         0.0 |   0.009381 |                   0.0 |                 0.0 |               0.0 | 0.136842 |             0.2 |        0.136842 |       0.11951 |            0.0 |  0.11951 |    0.037524 | 0.136842 |  0.11951 |
    | 08.01. |           0.0 |         0.0 |   0.009683 |                   0.0 |                 0.0 |               0.0 | 0.126316 |             0.2 |        0.126316 |      0.112348 |            0.0 | 0.112348 |    0.038731 | 0.126316 | 0.112348 |
    | 09.01. |           0.0 |         0.0 |    0.00993 |                   0.0 |                 0.0 |               0.0 | 0.115789 |             0.2 |        0.115789 |      0.104345 |            0.0 | 0.104345 |     0.03972 | 0.115789 | 0.104345 |
    | 10.01. |           0.0 |         0.0 |   0.010135 |                   0.0 |                 0.0 |               0.0 | 0.105263 |             0.2 |        0.105263 |      0.095788 |            0.0 | 0.095788 |    0.040538 | 0.105263 | 0.095788 |
    | 11.01. |           0.0 |         0.0 |   0.010305 |                   0.0 |                 0.0 |               0.0 | 0.094737 |             0.2 |        0.094737 |      0.086852 |            0.0 | 0.086852 |    0.041219 | 0.094737 | 0.086852 |
    | 12.01. |           0.0 |         0.0 |   0.010447 |                   0.0 |                 0.0 |               0.0 | 0.084211 |             0.2 |        0.084211 |      0.077648 |            0.0 | 0.077648 |    0.041786 | 0.084211 | 0.077648 |
    | 13.01. |           0.0 |         0.0 |   0.010564 |                   0.0 |                 0.0 |               0.0 | 0.073684 |             0.2 |        0.073684 |      0.068248 |            0.0 | 0.068248 |    0.042256 | 0.073684 | 0.068248 |
    | 14.01. |           0.0 |         0.0 |    0.01066 |                   0.0 |                 0.0 |               0.0 | 0.063158 |             0.2 |        0.063158 |      0.058705 |            0.0 | 0.058705 |    0.042641 | 0.063158 | 0.058705 |
    | 15.01. |           0.0 |         0.0 |   0.010737 |                   0.0 |                 0.0 |               0.0 | 0.052632 |             0.2 |        0.052632 |      0.049056 |            0.0 | 0.049056 |     0.04295 | 0.052632 | 0.049056 |
    | 16.01. |           0.0 |         0.0 |   0.010797 |                   0.0 |                 0.0 |               0.0 | 0.042105 |             0.2 |        0.042105 |      0.039328 |            0.0 | 0.039328 |     0.04319 | 0.042105 | 0.039328 |
    | 17.01. |           0.0 |         0.0 |   0.010841 |                   0.0 |                 0.0 |               0.0 | 0.031579 |             0.2 |        0.031579 |      0.029542 |            0.0 | 0.029542 |    0.043366 | 0.031579 | 0.029542 |
    | 18.01. |           0.0 |         0.0 |    0.01087 |                   0.0 |                 0.0 |               0.0 | 0.021053 |             0.2 |        0.021053 |      0.019715 |            0.0 | 0.019715 |    0.043481 | 0.021053 | 0.019715 |
    | 19.01. |           0.0 |         0.0 |   0.010885 |                   0.0 |                 0.0 |               0.0 | 0.010526 |             0.2 |        0.010526 |      0.009864 |            0.0 | 0.009864 |    0.043539 | 0.010526 | 0.009864 |
    | 20.01. |           0.0 |         0.0 |   0.010885 |                   0.0 |                 0.0 |               0.0 |      0.0 |             0.2 |             0.0 |           0.0 |            0.0 |      0.0 |    0.043539 |      0.0 |      0.0 |

.. _dam_v003_evaporation:

evaporation
___________

This example corresponds to the :ref:`dam_v001_evaporation` example of application model
|dam_v001| and the :ref:`dam_v002_evaporation` example of application model |dam_v002|.
We update the time series of potential evaporation and the required remote release
accordingly:

>>> inputs.evaporation.series = 10 * [1.0] + 10 * [5.0]

Due to the remaining differences regarding remote demand, the following results differ
from those of |dam_v001| and |dam_v002|.  However, detailed comparisons show the same
patterns for adjusting given potential evaporation and its conversion to actual
evaporation under water scarcity:

.. integration-test::

    >>> test("dam_v003_evaporation")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume |   inflow |  outflow |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         1.0 |   0.003206 |                   0.0 |               0.016 |          0.014663 |      0.2 |             0.2 |             0.2 |      0.036901 |            0.0 | 0.036901 |    0.012825 |      0.2 | 0.036901 |
    | 02.01. |           0.0 |         1.0 |   0.005186 |                   0.0 |              0.0192 |            0.0192 | 0.189474 |             0.2 |        0.189474 |      0.078604 |            0.0 | 0.078604 |    0.020745 | 0.189474 | 0.078604 |
    | 03.01. |           0.0 |         1.0 |   0.006342 |                   0.0 |             0.01984 |           0.01984 | 0.178947 |             0.2 |        0.178947 |      0.105594 |            0.0 | 0.105594 |    0.025369 | 0.178947 | 0.105594 |
    | 04.01. |           0.0 |         1.0 |   0.007036 |                   0.0 |            0.019968 |          0.019968 | 0.168421 |             0.2 |        0.168421 |       0.11633 |            0.0 |  0.11633 |    0.028144 | 0.168421 |  0.11633 |
    | 05.01. |           0.0 |         1.0 |   0.007486 |                   0.0 |            0.019994 |          0.019994 | 0.157895 |             0.2 |        0.157895 |      0.117074 |            0.0 | 0.117074 |    0.029944 | 0.157895 | 0.117074 |
    | 06.01. |           0.0 |         1.0 |    0.00778 |                   0.0 |            0.019999 |          0.019999 | 0.147368 |             0.2 |        0.147368 |      0.113734 |            0.0 | 0.113734 |    0.031122 | 0.147368 | 0.113734 |
    | 07.01. |           0.0 |         1.0 |   0.007969 |                   0.0 |                0.02 |              0.02 | 0.136842 |             0.2 |        0.136842 |      0.108123 |            0.0 | 0.108123 |    0.031875 | 0.136842 | 0.108123 |
    | 08.01. |           0.0 |         1.0 |    0.00808 |                   0.0 |                0.02 |              0.02 | 0.126316 |             0.2 |        0.126316 |      0.101174 |            0.0 | 0.101174 |    0.032319 | 0.126316 | 0.101174 |
    | 09.01. |           0.0 |         1.0 |   0.008131 |                   0.0 |                0.02 |              0.02 | 0.115789 |             0.2 |        0.115789 |      0.093398 |            0.0 | 0.093398 |    0.032526 | 0.115789 | 0.093398 |
    | 10.01. |           0.0 |         1.0 |   0.008135 |                   0.0 |                0.02 |              0.02 | 0.105263 |             0.2 |        0.105263 |      0.085098 |            0.0 | 0.085098 |     0.03254 | 0.105263 | 0.085098 |
    | 11.01. |           0.0 |         5.0 |   0.006837 |                   0.0 |               0.084 |             0.084 | 0.094737 |             0.2 |        0.094737 |      0.070849 |            0.0 | 0.070849 |    0.027347 | 0.094737 | 0.070849 |
    | 12.01. |           0.0 |         5.0 |   0.005443 |                   0.0 |              0.0968 |            0.0968 | 0.084211 |             0.2 |        0.084211 |       0.05191 |            0.0 |  0.05191 |    0.021774 | 0.084211 |  0.05191 |
    | 13.01. |           0.0 |         5.0 |   0.004141 |                   0.0 |             0.09936 |           0.09936 | 0.073684 |             0.2 |        0.073684 |      0.034602 |            0.0 | 0.034602 |    0.016566 | 0.073684 | 0.034602 |
    | 14.01. |           0.0 |         5.0 |   0.002892 |                   0.0 |            0.099872 |          0.099872 | 0.063158 |             0.2 |        0.063158 |      0.021137 |            0.0 | 0.021137 |    0.011567 | 0.063158 | 0.021137 |
    | 15.01. |           0.0 |         5.0 |   0.001617 |                   0.0 |            0.099974 |          0.099935 | 0.052632 |             0.2 |        0.052632 |      0.011726 |            0.0 | 0.011726 |    0.006467 | 0.052632 | 0.011726 |
    | 16.01. |           0.0 |         5.0 |   0.000334 |                   0.0 |            0.099995 |          0.095829 | 0.042105 |             0.2 |        0.042105 |      0.005681 |            0.0 | 0.005681 |    0.001335 | 0.042105 | 0.005681 |
    | 17.01. |           0.0 |         5.0 |  -0.000145 |                   0.0 |            0.099999 |          0.050858 | 0.031579 |             0.2 |        0.031579 |      0.002901 |            0.0 | 0.002901 |   -0.000582 | 0.031579 | 0.002901 |
    | 18.01. |           0.0 |         5.0 |  -0.000309 |                   0.0 |                 0.1 |          0.026856 | 0.021053 |             0.2 |        0.021053 |      0.001754 |            0.0 | 0.001754 |   -0.001235 | 0.021053 | 0.001754 |
    | 19.01. |           0.0 |         5.0 |    -0.0004 |                   0.0 |                 0.1 |          0.013935 | 0.010526 |             0.2 |        0.010526 |      0.000808 |            0.0 | 0.000808 |   -0.001599 | 0.010526 | 0.000808 |
    | 20.01. |           0.0 |         5.0 |   -0.00059 |                   0.0 |                 0.1 |          0.008828 |      0.0 |             0.2 |             0.0 |           0.0 |            0.0 |      0.0 |   -0.002362 |      0.0 |      0.0 |

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
>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 2.5]))
>>> inputs.precipitation.series = [0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inflow.sequences.sim.series = [0.0, 0.0, 5.0, 9.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inputs.evaporation.series = 0.0

The following results demonstrate that |dam_v003| calculates the same outflow values as
|dam_v001| and |dam_v002| if there is no relevant remote demand:

.. integration-test::

    >>> test("dam_v003_flood_retention")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |          50.0 |         0.0 |   0.021027 |                   1.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       0.026514 | 0.026514 |    0.084109 |    0.0 | 0.026514 |
    | 03.01. |           0.0 |         0.0 |   0.125058 |                   0.0 |                 0.0 |               0.0 |    5.0 |             0.0 |             0.0 |           0.0 |       0.183744 | 0.183744 |    0.500234 |    5.0 | 0.183744 |
    | 04.01. |           0.0 |         0.0 |    0.30773 |                   0.0 |                 0.0 |               0.0 |    9.0 |             0.0 |             0.0 |           0.0 |       0.542983 | 0.542983 |     1.23092 |    9.0 | 0.542983 |
    | 05.01. |           0.0 |         0.0 |   0.459772 |                   0.0 |                 0.0 |               0.0 |    8.0 |             0.0 |             0.0 |           0.0 |       0.961039 | 0.961039 |    1.839086 |    8.0 | 0.961039 |
    | 06.01. |           0.0 |         0.0 |   0.540739 |                   0.0 |                 0.0 |               0.0 |    5.0 |             0.0 |             0.0 |           0.0 |       1.251523 | 1.251523 |    2.162955 |    5.0 | 1.251523 |
    | 07.01. |           0.0 |         0.0 |   0.575395 |                   0.0 |                 0.0 |               0.0 |    3.0 |             0.0 |             0.0 |           0.0 |       1.395546 | 1.395546 |    2.301579 |    3.0 | 1.395546 |
    | 08.01. |           0.0 |         0.0 |   0.587202 |                   0.0 |                 0.0 |               0.0 |    2.0 |             0.0 |             0.0 |           0.0 |       1.453375 | 1.453375 |    2.348808 |    2.0 | 1.453375 |
    | 09.01. |           0.0 |         0.0 |   0.577361 |                   0.0 |                 0.0 |               0.0 |    1.0 |             0.0 |             0.0 |           0.0 |       1.455596 | 1.455596 |    2.309444 |    1.0 | 1.455596 |
    | 10.01. |           0.0 |         0.0 |    0.54701 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       1.405132 | 1.405132 |    2.188041 |    0.0 | 1.405132 |
    | 11.01. |           0.0 |         0.0 |   0.518255 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       1.331267 | 1.331267 |    2.073019 |    0.0 | 1.331267 |
    | 12.01. |           0.0 |         0.0 |   0.491011 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       1.261285 | 1.261285 |    1.964044 |    0.0 | 1.261285 |
    | 13.01. |           0.0 |         0.0 |     0.4652 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       1.194981 | 1.194981 |    1.860798 |    0.0 | 1.194981 |
    | 14.01. |           0.0 |         0.0 |   0.440745 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       1.132163 | 1.132163 |    1.762979 |    0.0 | 1.132163 |
    | 15.01. |           0.0 |         0.0 |   0.417576 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       1.072647 | 1.072647 |    1.670302 |    0.0 | 1.072647 |
    | 16.01. |           0.0 |         0.0 |   0.395624 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |        1.01626 |  1.01626 |    1.582498 |    0.0 |  1.01626 |
    | 17.01. |           0.0 |         0.0 |   0.374827 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       0.962837 | 0.962837 |    1.499308 |    0.0 | 0.962837 |
    | 18.01. |           0.0 |         0.0 |   0.355123 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       0.912222 | 0.912222 |    1.420492 |    0.0 | 0.912222 |
    | 19.01. |           0.0 |         0.0 |   0.336455 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       0.864268 | 0.864268 |     1.34582 |    0.0 | 0.864268 |
    | 20.01. |           0.0 |         0.0 |   0.318768 |                   0.0 |                 0.0 |               0.0 |    0.0 |             0.0 |             0.0 |           0.0 |       0.818835 | 0.818835 |    1.275072 |    0.0 | 0.818835 |
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
    """Version 0 of HydPy-Dam."""

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
        dam_model.Calc_RequiredRelease_V2,
        dam_model.Calc_TargetedRelease_V1,
    )
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V1,
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
    )
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
