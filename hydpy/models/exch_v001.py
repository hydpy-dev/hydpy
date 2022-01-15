# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Bidirectional water exchange over a weir.

.. _`German Federal Institute of Hydrology (BfG)`: https://www.bafg.de/EN

Version 1 of `HydPy-Exch` implements the general weir formula.  We implemented it on
behalf of the `German Federal Institute of Hydrology (BfG)`_ to connect different
|dam_v006| instances (lake models), enabling them to exchange water based on water
level differences.  This specific combination serves to model some huge, connected
(sub)lakes of the Rhine basin similar to HBV96 :cite:`ref-Lindstrom1997HBV96`.
Combinations with other models providing (something like) water level information and
allowing for an additional inflow that can be positive and negative are possible.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform all integration tests over a month with a simulation step of one day:

>>> from hydpy import Element, FusedVariable, Nodes, PPoly, prepare_model, pub
>>> pub.timegrids = "2000-01-01", "2000-02-01", "1d"

The following examples demonstrate how |exch_v001| interacts with lake models like
|dam_v006|.  Therefore, we must set up one |exch_v001| instance and two |dam_v006|
instances.

First, we define the eight required |Node| objects:

 * `inflow1` and `inflow2` pass the inflow into the first and the second lake.
 * `outflow1` and `outflow2` receive the lakes' outflows.
 * `overflow1` and `overflow2` exchange water between the lakes.
 * `waterlevel1` and `waterlevel2` inform the exchange model about the lakes' current
   water levels.

We define the |Node.variable| type of all nodes explicitly.  For the inflow and outflow
nodes, we stick to the default by using the string literal "Q", telling |dam_v006| to
connect these nodes to the inlet sequence |dam_inlets.Q| and outlet sequence
|dam_outlets.Q|, respectively:

>>> inflow1, inflow2  = Nodes("inflow1", "inflow2", defaultvariable="Q")
>>> outflow1, outflow2  = Nodes("outflow1", "outflow2", defaultvariable="Q")

The overflow nodes do not connect both lakes directly but the lakes with the exchange
model. Still, we can use a single string literal ("E") because the exchange-related
inlet sequence of |dam_v006| (|dam_inlets.E|) and the only outlet sequence of
|exch_v001| (|exch_outlets.E|) have the same name:

>>> overflow1, overflow2 = Nodes("overflow1", "overflow2", defaultvariable="E")

The water level nodes require a little more effort in first defining a |FusedVariable|.
This fused variable combines the string literal "L" (telling |exch_v001| to connect
both nodes to the receiver sequence |exch_receivers.L|) and the alias of output
sequence |dam_factors.WaterLevel| of |dam_v006|:

>>> from hydpy.outputs import dam_WaterLevel
>>> WaterLevel = FusedVariable("L", dam_WaterLevel)
>>> waterlevel1, waterlevel2 = Nodes("waterlevel1", "waterlevel2", defaultvariable=WaterLevel)

Now we prepare the two |Element| objects holding the |dam_v006| instances.  The
configuration is similar to the one in the documentation on |dam_v006|, except in
connecting `waterlevel1` and `waterlevel2` as additional output nodes:

>>> lake1 = Element("lake1",
...                 inlets=(inflow1, overflow1),
...                 outlets=outflow1,
...                 outputs=waterlevel1)
>>> lake2 = Element("lake2",
...                 inlets=(inflow2, overflow2),
...                 outlets=outflow2,
...                 outputs=waterlevel2)

From the perspective of the exchange element, `waterlevel1` and `waterlevel2` are
receiver nodes, while `overflow1` and `overflow2` are outlet nodes.  At the beginning
of each simulation step, |exch_v001| receives water level information from both lakes.
Then, it calculates the correct exchange and sends it to both lakes via the overflow
nodes, but with different signs.  If the first lake's water level is higher, it passes
a negative value to `overflow1` (the first lake loses water) and a positive value to
`overflow2` (the second lake gains water), and vice versa:

>>> exchange = Element("exchange",
...                    receivers=(waterlevel1, waterlevel2),
...                    outlets=(overflow1, overflow2))

In our test configuration, both the nodes' names and the order in which we give them to
the constructor of class |Element| agree with the nodes' target lakes.  This practice
seems advisable for keeping clarity, but it is not a technical requirement.  The
documentation on class |exch_v001.Model| explains the internal sorting mechanisms and
plausibility checks underlying the connection-related functionalities of |exch_v001|.

We parameterise both lake models identically. All of the following values stem from
the documentation on |dam_v006|.  We will use them in all examples:

>>> lake1.model = prepare_model("dam_v006")
>>> lake2.model = prepare_model("dam_v006")
>>> from numpy import inf
>>> for model_ in (lake1.model, lake2.model):
...     control = model_.parameters.control
...     control.catchmentarea(86.4)
...     control.surfacearea(1.44)
...     control.correctionprecipitation(1.2)
...     control.correctionevaporation(1.2)
...     control.weightevaporation(0.8)
...     control.thresholdevaporation(0.0)
...     control.dischargetolerance(0.1)
...     control.toleranceevaporation(0.001)
...     control.allowedwaterleveldrop(inf)
...     control.watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
...     control.pars.update()

Now we prepare the exchange model.  We will use common values for the flow coefficient
and exponent throughout the following examples:

>>> from hydpy.models.exch_v001 import *
>>> parameterstep("1d")
>>> flowcoefficient(0.62)
>>> flowexponent(1.5)
>>> exchange.model = model

An |IntegrationTest| object will help us to perform the individual examples:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(exchange)
>>> test.plotting_options.axis1 = (factors.waterlevel,)
>>> test.plotting_options.axis2 = (fluxes.potentialexchange, fluxes.actualexchange)

For simplicity, we set both lakes' inflow, precipitation, and evaporation to zero:

>>> inflow1.sequences.sim.series = 0.0
>>> inflow2.sequences.sim.series = 0.0
>>> for model_ in (lake1.model, lake2.model):
...     inputs = model_.sequences.inputs
...     for seq in (inputs.precipitation, inputs.evaporation):
...         seq.activate_ram()
...         seq.series = 0.0

The only difference between both lakes is their initial state.  The first lake starts
empty, and the second lake starts with a water volume of 1 million m³.  Note that
|exch_v001| requires the same information.  We must give it to the log sequence
|LoggedWaterLevel|:

>>> test.inits = [(lake1.model.sequences.states.watervolume, 0.0),
...               (lake1.model.sequences.logs.loggedadjustedevaporation, 0.0),
...               (lake2.model.sequences.states.watervolume, 1.0),
...               (lake2.model.sequences.logs.loggedadjustedevaporation, 0.0),
...               (logs.loggedwaterlevel, (0.0, 1.0))]

.. _exch_v001_base_scenario:

base scenario
_____________

Our base scenario defines a small crest width of 0.2 meters, enabling only limited
water exchange:

>>> crestwidth(0.2)

The crest height of 0.0 m and the allowed exchange of 5.0 m³/s are so low and high,
respectively, that they do not affect the following results:

>>> crestheight(0.0)
>>> allowedexchange(5.0)

We define a linear relationship between the water level and the outflow for both lakes:

>>> for model_ in (lake1.model, lake2.model):
...     model_.parameters.control.waterlevel2flooddischarge(
...         PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 2.0]))

The following results show that the first lake's water level drops fast due to releasing
water to the second lake and its outlet.  The second lake receives this overflow through
the whole simulation period but with a decreasing tendency.  Hence, the water level
rises initially but then falls again because of the lake's outflow:

.. integration-test::

    >>> test("exch_v001_base_scenario")
    |                date |           waterlevel | deltawaterlevel | potentialexchange | actualexchange | inflow1 | inflow2 | outflow1 | outflow2 | overflow1 | overflow2 | waterlevel1 | waterlevel2 |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-01-01 00:00:00 |      0.0         1.0 |            -1.0 |            -0.124 |         -0.124 |     0.0 |     0.0 | 0.010096 |   1.8266 |     0.124 |    -0.124 |    0.009841 |    0.831468 |
    | 2000-01-02 00:00:00 | 0.009841    0.831468 |       -0.821627 |         -0.092349 |      -0.092349 |     0.0 |     0.0 | 0.025961 | 1.520015 |  0.092349 | -0.092349 |    0.015577 |     0.69216 |
    | 2000-01-03 00:00:00 | 0.015577     0.69216 |       -0.676583 |         -0.069009 |      -0.069009 |     0.0 |     0.0 | 0.034425 | 1.265985 |  0.069009 | -0.069009 |    0.018565 |    0.576816 |
    | 2000-01-04 00:00:00 | 0.018565    0.576816 |       -0.558251 |         -0.051721 |      -0.051721 |     0.0 |     0.0 | 0.038391 | 1.055489 |  0.051721 | -0.051721 |    0.019717 |    0.481154 |
    | 2000-01-05 00:00:00 | 0.019717    0.481154 |       -0.461437 |         -0.038868 |      -0.038868 |     0.0 |     0.0 | 0.039385 | 0.880788 |  0.038868 | -0.038868 |    0.019672 |    0.401695 |
    | 2000-01-06 00:00:00 | 0.019672    0.401695 |       -0.382023 |         -0.029279 |      -0.029279 |     0.0 |     0.0 | 0.038475 | 0.735592 |  0.029279 | -0.029279 |    0.018878 |     0.33561 |
    | 2000-01-07 00:00:00 | 0.018878     0.33561 |       -0.316733 |         -0.022103 |      -0.022103 |     0.0 |     0.0 | 0.036403 | 0.614768 |  0.022103 | -0.022103 |    0.017642 |    0.280585 |
    | 2000-01-08 00:00:00 | 0.017642    0.280585 |       -0.262942 |         -0.016719 |      -0.016719 |     0.0 |     0.0 |  0.03368 | 0.514116 |  0.016719 | -0.016719 |    0.016177 |    0.234721 |
    | 2000-01-09 00:00:00 | 0.016177    0.234721 |       -0.218544 |         -0.012669 |      -0.012669 |     0.0 |     0.0 | 0.030653 | 0.430186 |  0.012669 | -0.012669 |    0.014623 |    0.196458 |
    | 2000-01-10 00:00:00 | 0.014623    0.196458 |       -0.181835 |         -0.009615 |      -0.009615 |     0.0 |     0.0 |  0.02755 |  0.36014 |  0.009615 | -0.009615 |    0.013073 |    0.164511 |
    | 2000-01-11 00:00:00 | 0.013073    0.164511 |       -0.151438 |         -0.007308 |      -0.007308 |     0.0 |     0.0 | 0.024519 | 0.301637 |  0.007308 | -0.007308 |    0.011586 |    0.137818 |
    | 2000-01-12 00:00:00 | 0.011586    0.137818 |       -0.126232 |         -0.005561 |      -0.005561 |     0.0 |     0.0 | 0.021651 |  0.25274 |  0.005561 | -0.005561 |    0.010196 |    0.115501 |
    | 2000-01-13 00:00:00 | 0.010196    0.115501 |       -0.105305 |         -0.004237 |      -0.004237 |     0.0 |     0.0 | 0.018997 | 0.211848 |  0.004237 | -0.004237 |    0.008921 |    0.096831 |
    | 2000-01-14 00:00:00 | 0.008921    0.096831 |        -0.08791 |         -0.003232 |      -0.003232 |     0.0 |     0.0 |  0.01658 | 0.177631 |  0.003232 | -0.003232 |    0.007768 |    0.081205 |
    | 2000-01-15 00:00:00 | 0.007768    0.081205 |       -0.073437 |         -0.002468 |      -0.002468 |     0.0 |     0.0 | 0.014406 | 0.148985 |  0.002468 | -0.002468 |    0.006736 |    0.068119 |
    | 2000-01-16 00:00:00 | 0.006736    0.068119 |       -0.061383 |         -0.001886 |      -0.001886 |     0.0 |     0.0 | 0.012471 | 0.124992 |  0.001886 | -0.001886 |    0.005822 |    0.057157 |
    | 2000-01-17 00:00:00 | 0.005822    0.057157 |       -0.051335 |         -0.001442 |      -0.001442 |     0.0 |     0.0 | 0.010762 | 0.104889 |  0.001442 | -0.001442 |    0.005016 |     0.04797 |
    | 2000-01-18 00:00:00 | 0.005016     0.04797 |       -0.042954 |         -0.001104 |      -0.001104 |     0.0 |     0.0 | 0.009261 | 0.087555 |  0.001104 | -0.001104 |    0.004312 |     0.04031 |
    | 2000-01-19 00:00:00 | 0.004312     0.04031 |       -0.035998 |         -0.000847 |      -0.000847 |     0.0 |     0.0 | 0.007951 | 0.073581 |  0.000847 | -0.000847 |    0.003698 |    0.033879 |
    | 2000-01-20 00:00:00 | 0.003698    0.033879 |       -0.030181 |          -0.00065 |       -0.00065 |     0.0 |     0.0 | 0.006813 | 0.061848 |   0.00065 |  -0.00065 |    0.003165 |    0.028479 |
    | 2000-01-21 00:00:00 | 0.003165    0.028479 |       -0.025314 |         -0.000499 |      -0.000499 |     0.0 |     0.0 | 0.005827 | 0.051994 |  0.000499 | -0.000499 |    0.002705 |    0.023944 |
    | 2000-01-22 00:00:00 | 0.002705    0.023944 |       -0.021239 |         -0.000384 |      -0.000384 |     0.0 |     0.0 | 0.004976 | 0.043717 |  0.000384 | -0.000384 |    0.002308 |    0.020134 |
    | 2000-01-23 00:00:00 | 0.002308    0.020134 |       -0.017825 |         -0.000295 |      -0.000295 |     0.0 |     0.0 | 0.004243 | 0.036763 |  0.000295 | -0.000295 |    0.001967 |    0.016932 |
    | 2000-01-24 00:00:00 | 0.001967    0.016932 |       -0.014965 |         -0.000227 |      -0.000227 |     0.0 |     0.0 | 0.003614 | 0.030918 |  0.000227 | -0.000227 |    0.001675 |    0.014241 |
    | 2000-01-25 00:00:00 | 0.001675    0.014241 |       -0.012566 |         -0.000175 |      -0.000175 |     0.0 |     0.0 | 0.003075 | 0.026006 |  0.000175 | -0.000175 |    0.001424 |    0.011979 |
    | 2000-01-26 00:00:00 | 0.001424    0.011979 |       -0.010555 |         -0.000134 |      -0.000134 |     0.0 |     0.0 | 0.002613 | 0.021876 |  0.000134 | -0.000134 |     0.00121 |    0.010077 |
    | 2000-01-27 00:00:00 |  0.00121    0.010077 |       -0.008867 |         -0.000104 |      -0.000104 |     0.0 |     0.0 | 0.002219 | 0.018404 |  0.000104 | -0.000104 |    0.001027 |    0.008478 |
    | 2000-01-28 00:00:00 | 0.001027    0.008478 |       -0.007451 |          -0.00008 |       -0.00008 |     0.0 |     0.0 | 0.001883 | 0.015484 |   0.00008 |  -0.00008 |    0.000871 |    0.007133 |
    | 2000-01-29 00:00:00 | 0.000871    0.007133 |       -0.006262 |         -0.000061 |      -0.000061 |     0.0 |     0.0 | 0.001597 | 0.013029 |  0.000061 | -0.000061 |    0.000738 |    0.006002 |
    | 2000-01-30 00:00:00 | 0.000738    0.006002 |       -0.005264 |         -0.000047 |      -0.000047 |     0.0 |     0.0 | 0.001353 | 0.010963 |  0.000047 | -0.000047 |    0.000626 |    0.005051 |
    | 2000-01-31 00:00:00 | 0.000626    0.005051 |       -0.004425 |         -0.000037 |      -0.000037 |     0.0 |     0.0 | 0.001146 | 0.009226 |  0.000037 | -0.000037 |     0.00053 |    0.004251 |

.. _exch_v001_crest_height:

crest height
____________

In this example, we increase the crest's width and, more importantly, set its height to
0.5 m, matching a water volume of 0.5 million m³:

>>> crestwidth(20.0)
>>> crestheight(0.5)

The crest height now influences the lakes' interaction significantly.  For
clarification, we disallow both lakes to release any water:

>>> for model_ in (lake1.model, lake2.model):
...     model_.parameters.control.waterlevel2flooddischarge(
...         PPoly.from_data(xs=[0.0], ys=[0.0]))


Due to the identical parameter values of both models and the symmetrical initial
conditions of 0.0 and 1.0 million m³, both water levels move towards the defined crest
height asymptotically:

.. integration-test::

    >>> test("exch_v001_crest_height")
    |                date |           waterlevel | deltawaterlevel | potentialexchange | actualexchange | inflow1 | inflow2 | outflow1 | outflow2 | overflow1 | overflow2 | waterlevel1 | waterlevel2 |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-01-01 00:00:00 |      0.0         1.0 |            -0.5 |         -4.384062 |      -4.384062 |     0.0 |     0.0 |      0.0 |      0.0 |  4.384062 | -4.384062 |    0.378783 |    0.621217 |
    | 2000-01-02 00:00:00 | 0.378783    0.621217 |       -0.121217 |          -0.52332 |       -0.52332 |     0.0 |     0.0 |      0.0 |      0.0 |   0.52332 |  -0.52332 |    0.423998 |    0.576002 |
    | 2000-01-03 00:00:00 | 0.423998    0.576002 |       -0.076002 |         -0.259813 |      -0.259813 |     0.0 |     0.0 |      0.0 |      0.0 |  0.259813 | -0.259813 |    0.446446 |    0.553554 |
    | 2000-01-04 00:00:00 | 0.446446    0.553554 |       -0.053554 |         -0.153679 |      -0.153679 |     0.0 |     0.0 |      0.0 |      0.0 |  0.153679 | -0.153679 |    0.459723 |    0.540277 |
    | 2000-01-05 00:00:00 | 0.459723    0.540277 |       -0.040277 |          -0.10023 |       -0.10023 |     0.0 |     0.0 |      0.0 |      0.0 |   0.10023 |  -0.10023 |    0.468383 |    0.531617 |
    | 2000-01-06 00:00:00 | 0.468383    0.531617 |       -0.031617 |          -0.06971 |       -0.06971 |     0.0 |     0.0 |      0.0 |      0.0 |   0.06971 |  -0.06971 |    0.474406 |    0.525594 |
    | 2000-01-07 00:00:00 | 0.474406    0.525594 |       -0.025594 |         -0.050772 |      -0.050772 |     0.0 |     0.0 |      0.0 |      0.0 |  0.050772 | -0.050772 |    0.478793 |    0.521207 |
    | 2000-01-08 00:00:00 | 0.478793    0.521207 |       -0.021207 |         -0.038295 |      -0.038295 |     0.0 |     0.0 |      0.0 |      0.0 |  0.038295 | -0.038295 |    0.482102 |    0.517898 |
    | 2000-01-09 00:00:00 | 0.482102    0.517898 |       -0.017898 |         -0.029692 |      -0.029692 |     0.0 |     0.0 |      0.0 |      0.0 |  0.029692 | -0.029692 |    0.484667 |    0.515333 |
    | 2000-01-10 00:00:00 | 0.484667    0.515333 |       -0.015333 |         -0.023543 |      -0.023543 |     0.0 |     0.0 |      0.0 |      0.0 |  0.023543 | -0.023543 |    0.486701 |    0.513299 |
    | 2000-01-11 00:00:00 | 0.486701    0.513299 |       -0.013299 |         -0.019017 |      -0.019017 |     0.0 |     0.0 |      0.0 |      0.0 |  0.019017 | -0.019017 |    0.488344 |    0.511656 |
    | 2000-01-12 00:00:00 | 0.488344    0.511656 |       -0.011656 |         -0.015604 |      -0.015604 |     0.0 |     0.0 |      0.0 |      0.0 |  0.015604 | -0.015604 |    0.489692 |    0.510308 |
    | 2000-01-13 00:00:00 | 0.489692    0.510308 |       -0.010308 |         -0.012976 |      -0.012976 |     0.0 |     0.0 |      0.0 |      0.0 |  0.012976 | -0.012976 |    0.490814 |    0.509186 |
    | 2000-01-14 00:00:00 | 0.490814    0.509186 |       -0.009186 |         -0.010918 |      -0.010918 |     0.0 |     0.0 |      0.0 |      0.0 |  0.010918 | -0.010918 |    0.491757 |    0.508243 |
    | 2000-01-15 00:00:00 | 0.491757    0.508243 |       -0.008243 |          -0.00928 |       -0.00928 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00928 |  -0.00928 |    0.492559 |    0.507441 |
    | 2000-01-16 00:00:00 | 0.492559    0.507441 |       -0.007441 |          -0.00796 |       -0.00796 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00796 |  -0.00796 |    0.493246 |    0.506754 |
    | 2000-01-17 00:00:00 | 0.493246    0.506754 |       -0.006754 |         -0.006882 |      -0.006882 |     0.0 |     0.0 |      0.0 |      0.0 |  0.006882 | -0.006882 |    0.493841 |    0.506159 |
    | 2000-01-18 00:00:00 | 0.493841    0.506159 |       -0.006159 |         -0.005994 |      -0.005994 |     0.0 |     0.0 |      0.0 |      0.0 |  0.005994 | -0.005994 |    0.494359 |    0.505641 |
    | 2000-01-19 00:00:00 | 0.494359    0.505641 |       -0.005641 |         -0.005254 |      -0.005254 |     0.0 |     0.0 |      0.0 |      0.0 |  0.005254 | -0.005254 |    0.494813 |    0.505187 |
    | 2000-01-20 00:00:00 | 0.494813    0.505187 |       -0.005187 |         -0.004633 |      -0.004633 |     0.0 |     0.0 |      0.0 |      0.0 |  0.004633 | -0.004633 |    0.495213 |    0.504787 |
    | 2000-01-21 00:00:00 | 0.495213    0.504787 |       -0.004787 |         -0.004107 |      -0.004107 |     0.0 |     0.0 |      0.0 |      0.0 |  0.004107 | -0.004107 |    0.495568 |    0.504432 |
    | 2000-01-22 00:00:00 | 0.495568    0.504432 |       -0.004432 |         -0.003659 |      -0.003659 |     0.0 |     0.0 |      0.0 |      0.0 |  0.003659 | -0.003659 |    0.495884 |    0.504116 |
    | 2000-01-23 00:00:00 | 0.495884    0.504116 |       -0.004116 |         -0.003274 |      -0.003274 |     0.0 |     0.0 |      0.0 |      0.0 |  0.003274 | -0.003274 |    0.496167 |    0.503833 |
    | 2000-01-24 00:00:00 | 0.496167    0.503833 |       -0.003833 |         -0.002943 |      -0.002943 |     0.0 |     0.0 |      0.0 |      0.0 |  0.002943 | -0.002943 |    0.496421 |    0.503579 |
    | 2000-01-25 00:00:00 | 0.496421    0.503579 |       -0.003579 |         -0.002655 |      -0.002655 |     0.0 |     0.0 |      0.0 |      0.0 |  0.002655 | -0.002655 |    0.496651 |    0.503349 |
    | 2000-01-26 00:00:00 | 0.496651    0.503349 |       -0.003349 |         -0.002404 |      -0.002404 |     0.0 |     0.0 |      0.0 |      0.0 |  0.002404 | -0.002404 |    0.496858 |    0.503142 |
    | 2000-01-27 00:00:00 | 0.496858    0.503142 |       -0.003142 |         -0.002184 |      -0.002184 |     0.0 |     0.0 |      0.0 |      0.0 |  0.002184 | -0.002184 |    0.497047 |    0.502953 |
    | 2000-01-28 00:00:00 | 0.497047    0.502953 |       -0.002953 |          -0.00199 |       -0.00199 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00199 |  -0.00199 |    0.497219 |    0.502781 |
    | 2000-01-29 00:00:00 | 0.497219    0.502781 |       -0.002781 |         -0.001819 |      -0.001819 |     0.0 |     0.0 |      0.0 |      0.0 |  0.001819 | -0.001819 |    0.497376 |    0.502624 |
    | 2000-01-30 00:00:00 | 0.497376    0.502624 |       -0.002624 |         -0.001667 |      -0.001667 |     0.0 |     0.0 |      0.0 |      0.0 |  0.001667 | -0.001667 |     0.49752 |     0.50248 |
    | 2000-01-31 00:00:00 |  0.49752     0.50248 |        -0.00248 |         -0.001531 |      -0.001531 |     0.0 |     0.0 |      0.0 |      0.0 |  0.001531 | -0.001531 |    0.497652 |    0.502348 |

.. _exch_v001_numerical_accuracy:

numerical accuracy
__________________

|exch_v001| is a very flexible tool but requires the user to apply it wisely.  One
crucial aspect is numerical accuracy.  One can expect sufficiently accurate results
only if the simulation step size is relatively short compared to water level dynamics.
In this example, we illustrate what happens if there is too much exchange due to a
large crest width:

>>> crestwidth(200.0)

We see substantial numerical oscillations in the results.  Due to the stiffness of the
underlying system of differential equations, a further increase of the crest width
would even result in a numerical overflow error that might be hard to trace back in a
real-world application:

.. integration-test::

    >>> test("exch_v001_numerical_accuracy")
    |                date |           waterlevel | deltawaterlevel | potentialexchange | actualexchange | inflow1 | inflow2 | outflow1 | outflow2 | overflow1 | overflow2 | waterlevel1 | waterlevel2 |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-01-01 00:00:00 |      0.0         1.0 |            -0.5 |         -43.84062 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |       0.432 |       0.568 |
    | 2000-01-02 00:00:00 |    0.432       0.568 |          -0.068 |         -2.198797 |      -2.198797 |     0.0 |     0.0 |      0.0 |      0.0 |  2.198797 | -2.198797 |    0.621976 |    0.378024 |
    | 2000-01-03 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-04 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-05 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-06 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-07 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-08 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-09 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-10 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-11 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-12 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-13 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-14 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-15 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-16 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-17 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-18 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-19 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-20 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-21 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-22 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-23 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-24 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-25 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-26 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-27 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-28 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-29 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |
    | 2000-01-30 00:00:00 | 0.189976    0.810024 |       -0.310024 |        -21.404969 |           -5.0 |     0.0 |     0.0 |      0.0 |      0.0 |       5.0 |      -5.0 |    0.621976 |    0.378024 |
    | 2000-01-31 00:00:00 | 0.621976    0.378024 |        0.121976 |          5.282426 |            5.0 |     0.0 |     0.0 |      0.0 |      0.0 |      -5.0 |       5.0 |    0.189976 |    0.810024 |

.. _exch_v001_allowed_exchange:

allowed exchange
________________

Sometimes there might be hydrological reasons to limit the water exchange.  Still, here
we use the related parameter |AllowedExchange| only as a stop-gap for stabilising
simulation results affected by numerical instability by setting its value to 2.0 m³/s:

>>> allowedexchange(2.0)

The results are far from perfect (the initial water levels change too slowly and still
oscillate for a few days) but are at least stable and not overly wrong:

.. integration-test::

    >>> test("exch_v001_allowed_exchange")
    |                date |           waterlevel | deltawaterlevel | potentialexchange | actualexchange | inflow1 | inflow2 | outflow1 | outflow2 | overflow1 | overflow2 | waterlevel1 | waterlevel2 |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-01-01 00:00:00 |      0.0         1.0 |            -0.5 |         -43.84062 |           -2.0 |     0.0 |     0.0 |      0.0 |      0.0 |       2.0 |      -2.0 |      0.1728 |      0.8272 |
    | 2000-01-02 00:00:00 |   0.1728      0.8272 |         -0.3272 |        -23.208209 |           -2.0 |     0.0 |     0.0 |      0.0 |      0.0 |       2.0 |      -2.0 |      0.3456 |      0.6544 |
    | 2000-01-03 00:00:00 |   0.3456      0.6544 |         -0.1544 |         -7.523027 |           -2.0 |     0.0 |     0.0 |      0.0 |      0.0 |       2.0 |      -2.0 |      0.5184 |      0.4816 |
    | 2000-01-04 00:00:00 |   0.5184      0.4816 |          0.0184 |          0.309491 |       0.309491 |     0.0 |     0.0 |      0.0 |      0.0 | -0.309491 |  0.309491 |     0.49166 |     0.50834 |
    | 2000-01-05 00:00:00 |  0.49166     0.50834 |        -0.00834 |         -0.094444 |      -0.094444 |     0.0 |     0.0 |      0.0 |      0.0 |  0.094444 | -0.094444 |     0.49982 |     0.50018 |
    | 2000-01-06 00:00:00 |  0.49982     0.50018 |        -0.00018 |           -0.0003 |        -0.0003 |     0.0 |     0.0 |      0.0 |      0.0 |    0.0003 |   -0.0003 |    0.499846 |    0.500154 |
    | 2000-01-07 00:00:00 | 0.499846    0.500154 |       -0.000154 |         -0.000237 |      -0.000237 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000237 | -0.000237 |    0.499866 |    0.500134 |
    | 2000-01-08 00:00:00 | 0.499866    0.500134 |       -0.000134 |         -0.000192 |      -0.000192 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000192 | -0.000192 |    0.499883 |    0.500117 |
    | 2000-01-09 00:00:00 | 0.499883    0.500117 |       -0.000117 |         -0.000157 |      -0.000157 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000157 | -0.000157 |    0.499896 |    0.500104 |
    | 2000-01-10 00:00:00 | 0.499896    0.500104 |       -0.000104 |         -0.000131 |      -0.000131 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000131 | -0.000131 |    0.499908 |    0.500092 |
    | 2000-01-11 00:00:00 | 0.499908    0.500092 |       -0.000092 |          -0.00011 |       -0.00011 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00011 |  -0.00011 |    0.499917 |    0.500083 |
    | 2000-01-12 00:00:00 | 0.499917    0.500083 |       -0.000083 |         -0.000093 |      -0.000093 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000093 | -0.000093 |    0.499925 |    0.500075 |
    | 2000-01-13 00:00:00 | 0.499925    0.500075 |       -0.000075 |          -0.00008 |       -0.00008 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00008 |  -0.00008 |    0.499932 |    0.500068 |
    | 2000-01-14 00:00:00 | 0.499932    0.500068 |       -0.000068 |         -0.000069 |      -0.000069 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000069 | -0.000069 |    0.499938 |    0.500062 |
    | 2000-01-15 00:00:00 | 0.499938    0.500062 |       -0.000062 |          -0.00006 |       -0.00006 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00006 |  -0.00006 |    0.499943 |    0.500057 |
    | 2000-01-16 00:00:00 | 0.499943    0.500057 |       -0.000057 |         -0.000053 |      -0.000053 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000053 | -0.000053 |    0.499948 |    0.500052 |
    | 2000-01-17 00:00:00 | 0.499948    0.500052 |       -0.000052 |         -0.000047 |      -0.000047 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000047 | -0.000047 |    0.499952 |    0.500048 |
    | 2000-01-18 00:00:00 | 0.499952    0.500048 |       -0.000048 |         -0.000041 |      -0.000041 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000041 | -0.000041 |    0.499956 |    0.500044 |
    | 2000-01-19 00:00:00 | 0.499956    0.500044 |       -0.000044 |         -0.000037 |      -0.000037 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000037 | -0.000037 |    0.499959 |    0.500041 |
    | 2000-01-20 00:00:00 | 0.499959    0.500041 |       -0.000041 |         -0.000033 |      -0.000033 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000033 | -0.000033 |    0.499962 |    0.500038 |
    | 2000-01-21 00:00:00 | 0.499962    0.500038 |       -0.000038 |          -0.00003 |       -0.00003 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00003 |  -0.00003 |    0.499964 |    0.500036 |
    | 2000-01-22 00:00:00 | 0.499964    0.500036 |       -0.000036 |         -0.000027 |      -0.000027 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000027 | -0.000027 |    0.499966 |    0.500034 |
    | 2000-01-23 00:00:00 | 0.499966    0.500034 |       -0.000034 |         -0.000024 |      -0.000024 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000024 | -0.000024 |    0.499969 |    0.500031 |
    | 2000-01-24 00:00:00 | 0.499969    0.500031 |       -0.000031 |         -0.000022 |      -0.000022 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000022 | -0.000022 |     0.49997 |     0.50003 |
    | 2000-01-25 00:00:00 |  0.49997     0.50003 |        -0.00003 |          -0.00002 |       -0.00002 |     0.0 |     0.0 |      0.0 |      0.0 |   0.00002 |  -0.00002 |    0.499972 |    0.500028 |
    | 2000-01-26 00:00:00 | 0.499972    0.500028 |       -0.000028 |         -0.000018 |      -0.000018 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000018 | -0.000018 |    0.499974 |    0.500026 |
    | 2000-01-27 00:00:00 | 0.499974    0.500026 |       -0.000026 |         -0.000017 |      -0.000017 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000017 | -0.000017 |    0.499975 |    0.500025 |
    | 2000-01-28 00:00:00 | 0.499975    0.500025 |       -0.000025 |         -0.000015 |      -0.000015 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000015 | -0.000015 |    0.499976 |    0.500024 |
    | 2000-01-29 00:00:00 | 0.499976    0.500024 |       -0.000024 |         -0.000014 |      -0.000014 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000014 | -0.000014 |    0.499978 |    0.500022 |
    | 2000-01-30 00:00:00 | 0.499978    0.500022 |       -0.000022 |         -0.000013 |      -0.000013 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000013 | -0.000013 |    0.499979 |    0.500021 |
    | 2000-01-31 00:00:00 | 0.499979    0.500021 |       -0.000021 |         -0.000012 |      -0.000012 |     0.0 |     0.0 |      0.0 |      0.0 |  0.000012 | -0.000012 |     0.49998 |     0.50002 |
"""
# import...

# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.models.exch import exch_model


class Model(modeltools.AdHocModel):
    """Version 1 of the `HydPy-Exch`.

    Before continuing, please first read the general documentation on application model
    |exch_v001|.

    To work correctly, each |exch_v001| must know which water level node and which
    overflow node belong to the same lake model.  The following examples might provide
    insight into how we deal with this issue but are merely there for testing that we
    handle all expected cases well.

    We recreate the configuration of the |Node| and |Element| objects of the main
    documentation, neglecting the lakes' inflow and outflow nodes, which are not
    relevant for connecting |exch_v001|:

    >>> from hydpy.models.exch_v001 import *
    >>> parameterstep()
    >>> from hydpy import Element, FusedVariable, Node, Nodes
    >>> from hydpy.outputs import dam_WaterLevel
    >>> WaterLevel = FusedVariable("L", dam_WaterLevel)

    >>> Element.clear_all()
    >>> Node.clear_all()

    >>> overflow1, overflow2 = Nodes("overflow1", "overflow2", defaultvariable="E")
    >>> waterlevel1, waterlevel2 = Nodes("waterlevel1", "waterlevel2", defaultvariable=WaterLevel)
    >>> lake1 = Element("lake1", inlets=overflow1, outputs=waterlevel1)
    >>> lake2 = Element("lake2", inlets=overflow2, outputs=waterlevel2)
    >>> exchange = Element("exchange",
    ...                    receivers=(waterlevel1, waterlevel2),
    ...                    outlets=(overflow1, overflow2))
    >>> exchange.model = model

    The water levels of `lake1` and `lake2` are available via the first and the second
    entry of the receiver sequence |exch_receivers.L|, respectively:

    >>> waterlevel1.sequences.sim = 1.0
    >>> waterlevel2.sequences.sim = 2.0
    >>> receivers.l
    l(1.0, 2.0)

    Likewise, the first and the second entry of the outlet sequence |exch_outlets.E|
    are available to the overflow nodes `lake1` and `lake2`, respectively:

    >>> outlets.e = 3.0, 4.0
    >>> overflow1.sequences.sim
    sim(3.0)
    >>> overflow2.sequences.sim
    sim(4.0)

    We recreate this configuration multiple times, each time changing one aspect
    (marked by exclamation marks).  First, we connect node `waterlevel2` with èlement
    `lake1` and node `waterlevel1` with element `lake2`:

    >>> Element.clear_all()
    >>> Node.clear_all()
    >>> overflow1, overflow2 = Nodes("overflow1", "overflow2", defaultvariable="E")
    >>> waterlevel1, waterlevel2 = Nodes("waterlevel1", "waterlevel2", defaultvariable=WaterLevel)
    >>> lake1 = Element("lake1", inlets=overflow1, outputs=waterlevel2)  # !!!
    >>> lake2 = Element("lake2", inlets=overflow2, outputs=waterlevel1)  # !!!
    >>> exchange = Element("exchange",
    ...                    receivers=(waterlevel1, waterlevel2),
    ...                    outlets=(overflow1, overflow2))
    >>> exchange.model = model

    Due to this swap, the first of the outlet sequence |exch_outlets.E| connects to
    node `overflow2` and the second one to node `overflow1`:

    >>> waterlevel1.sequences.sim = 1.0
    >>> waterlevel2.sequences.sim = 2.0
    >>> receivers.l
    l(1.0, 2.0)

    >>> outlets.e = 3.0, 4.0
    >>> overflow1.sequences.sim
    sim(4.0)
    >>> overflow2.sequences.sim
    sim(3.0)

    Swapping the nodes `overflow1` and `overflow2` instead of `waterlevel1` and
    `waterlevel2` leads to the same results (we arbitrarily decided to ground the
    internal sorting on the alphabetical order of the receiver nodes' names):

    >>> Element.clear_all()
    >>> Node.clear_all()
    >>> overflow1, overflow2 = Nodes("overflow1", "overflow2", defaultvariable="E")
    >>> waterlevel1, waterlevel2 = Nodes("waterlevel1", "waterlevel2", defaultvariable=WaterLevel)
    >>> lake1 = Element("lake1", inlets=overflow2, outputs=waterlevel1)  # !!!
    >>> lake2 = Element("lake2", inlets=overflow1, outputs=waterlevel2)  # !!!
    >>> exchange = Element("exchange",
    ...                    receivers=(waterlevel1, waterlevel2),
    ...                    outlets=(overflow1, overflow2))
    >>> exchange.model = model

    >>> waterlevel1.sequences.sim = 1.0
    >>> waterlevel2.sequences.sim = 2.0
    >>> receivers.l
    l(1.0, 2.0)

    >>> outlets.e = 3.0, 4.0
    >>> overflow1.sequences.sim
    sim(4.0)
    >>> overflow2.sequences.sim
    sim(3.0)

    Now we (accidentally) connect node `waterlevel2` to both lakes.  Therefore,
    |exch_v001| cannot find a water level node connected to the same lake model as
    outlet node `overflow1`:

    >>> Element.clear_all()
    >>> Node.clear_all()
    >>> overflow1, overflow2 = Nodes("overflow1", "overflow2", defaultvariable="E")
    >>> waterlevel1, waterlevel2 = Nodes("waterlevel1", "waterlevel2", defaultvariable=WaterLevel)
    >>> lake1 = Element("lake1", inlets=overflow1, outputs=waterlevel2)  # !!!
    >>> lake2 = Element("lake2", inlets=overflow2, outputs=waterlevel2)
    >>> exchange = Element("exchange",
    ...                    receivers=(waterlevel1, waterlevel2),
    ...                    outlets=(overflow1, overflow2))
    >>> exchange.model = model
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to build the node connection of the `outlet` sequences \
of the model handled by element `exchange`, the following error occurred: Outlet node \
`overflow1` does not correspond to any available receiver node.

    |exch_v001| raises the following error if there are not precisely two water level
    nodes available:

    >>> Element.clear_all()
    >>> Node.clear_all()
    >>> overflow1, overflow2 = Nodes("overflow1", "overflow2", defaultvariable="E")
    >>> waterlevel1, waterlevel2 = Nodes("waterlevel1", "waterlevel2", defaultvariable=WaterLevel)
    >>> lake1 = Element("lake1", inlets=overflow1, outputs=waterlevel1)
    >>> lake2 = Element("lake2", inlets=overflow2, outputs=waterlevel2)
    >>> exchange = Element("exchange",
    ...                    receivers=waterlevel1,  # !!!
    ...                    outlets=(overflow1, overflow2))
    >>> exchange.model = model
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to build the node connection of the `receiver` \
sequences of the model handled by element `exchange`, the following error occurred: \
There must be exactly 2 outlet receiver but the following `1` receiver nodes are \
defined: waterlevel1.

    Correspondingly, |exch_v001| raises the following error if there are not precisely
    two overflow nodes available:

    >>> Element.clear_all()
    >>> Node.clear_all()
    >>> overflow1, overflow2 = Nodes("overflow1", "overflow2", defaultvariable="E")
    >>> waterlevel1, waterlevel2 = Nodes("waterlevel1", "waterlevel2", defaultvariable=WaterLevel)
    >>> lake1 = Element("lake1", inlets=overflow1, outputs=waterlevel1)
    >>> lake2 = Element("lake2", inlets=overflow2, outputs=waterlevel2)
    >>> exchange = Element("exchange",
    ...                    receivers=(waterlevel1, waterlevel2),
    ...                    outlets=(overflow1, overflow2, waterlevel2))  # !!!
    >>> exchange.model = model
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to build the node connection of the `outlet` sequences \
of the model handled by element `exchange`, the following error occurred: There must \
be exactly 2 outlet nodes but the following `3` outlet nodes are defined: overflow1, \
overflow2, and waterlevel2.
    """

    INLET_METHODS = ()
    RECEIVER_METHODS = (exch_model.Pic_LoggedWaterLevel_V1,)
    RUN_METHODS = (
        exch_model.Update_WaterLevel_V1,
        exch_model.Calc_DeltaWaterLevel_V1,
        exch_model.Calc_PotentialExchange_V1,
        exch_model.Calc_ActualExchange_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (exch_model.Pass_ActualExchange_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()

    def _connect_receivers(self) -> None:
        element = self.element
        assert element is not None
        receivers = element.receivers
        if len(receivers) != 2:
            raise RuntimeError(
                f"There must be exactly 2 outlet receiver but the following "
                f"`{len(receivers)}` receiver nodes are defined: "
                f"{objecttools.enumeration(node.name for node in receivers)}."
            )
        super()._connect_receivers()

    def _connect_outlets(self) -> None:
        element = self.element
        assert element is not None
        outlets = element.outlets
        if len(outlets) != 2:
            raise RuntimeError(
                f"There must be exactly 2 outlet nodes but the following "
                f"`{len(outlets)}` outlet nodes are defined: "
                f"{objecttools.enumeration(node.name for node in outlets)}."
            )
        idx2outlets = {}
        for outlet in outlets:
            for idx, receiver in enumerate(element.receivers):
                if outlet.exits == receiver.entries:
                    idx2outlets[idx] = outlet
                    break
            else:
                raise RuntimeError(
                    f"Outlet node `{outlet.name}` does not correspond to any "
                    f"available receiver node."
                )
        sequence = element.model.sequences.outlets["e"]
        sequence.shape = 2
        for idx, outlet in idx2outlets.items():
            sequence.set_pointer(outlet.get_double("outlets"), idx)


tester = Tester()
cythonizer = Cythonizer()
