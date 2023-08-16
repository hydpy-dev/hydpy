# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Retention basin version of HydPy-Dam.

.. _`LARSIM`: http://www.larsim.de/en/the-model/

|dam_v007| is a simple "retention basin" model, similar to the "RUEC" model of
`LARSIM`_.  One can understand it as an extension of |dam_v006|, and it partly requires
equal specifications.  Hence, before continuing, please first read the documentation on
|dam_v006|.

In extension to |dam_v006|, |dam_v007| implements the control parameter |AllowedRelease|
(and the related parameters |WaterLevelMinimumThreshold| and
|WaterLevelMinimumTolerance|).  Usually, one takes the discharge not causing any harm
downstream as the "allowed release", making |dam_v007| behave like a retention basin
without active control.  However, one can vary the allowed release seasonally
(|AllowedRelease| inherits from class |SeasonalParameter|).

In contrast to |dam_v006|, |dam_v007| does not allow to restrict the speed of the water
level decrease during periods with little inflow and thus does not use the parameter
|AllowedWaterLevelDrop|.

Integration tests
=================

.. how_to_understand_integration_tests::

We create the same test set as for application model |dam_v006|, including identical
input series and an identical relationship between stage and volume:

>>> from hydpy import IntegrationTest, Element, pub
>>> pub.timegrids = "01.01.2000", "21.01.2000", "1d"
>>> parameterstep("1d")
>>> element = Element("element", inlets="input_", outlets="output")
>>> element.model = model
>>> test = IntegrationTest(element)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume
>>> test.inits = [
...     (states.watervolume, 0.0),
...     (logs.loggedadjustedevaporation, 0.0)]
>>> test.reset_inits()
>>> conditions = model.conditions
>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
>>> surfacearea(1.44)
>>> catchmentarea(86.4)
>>> correctionprecipitation(1.2)
>>> correctionevaporation(1.2)
>>> weightevaporation(0.8)
>>> thresholdevaporation(0.0)
>>> toleranceevaporation(0.001)
>>> inputs.precipitation.series = [
...     0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> element.inlets.input_.sequences.sim.series = [
...     0.0, 0.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inputs.evaporation.series = 0.0

.. _dam_v007_base_scenario:

base scenario
_____________

To show that |dam_v007| extends |dam_v006| correctly, we also define the same
quasi-linear relation between discharge and stage used throughout the integration tests
of |dam_v006| and additionally set the allowed release to 0 m³/s (which makes the values
of the two water-related control parameters irrelevant).  As expected, |dam_v007| now
calculates outflow values identical with the ones of the :ref:`dam_v006_base_scenario`
example of |dam_v006| (where |AllowedWaterLevelDrop| is |numpy.inf|):

.. integration-test::

    >>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 10.0]))
    >>> allowedrelease(0.0)
    >>> waterlevelminimumtolerance(0.1)
    >>> waterlevelminimumthreshold(0.0)
    >>> test("dam_v007_base_scenario")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |          50.0 |         0.0 |   0.057904 |                   1.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.329814 | 0.329814 |    0.057904 |    0.0 | 0.329814 |
    | 03.01. |           0.0 |         0.0 |   0.371486 |                   0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       2.370574 | 2.370574 |    0.371486 |    6.0 | 2.370574 |
    | 04.01. |           0.0 |         0.0 |   0.850751 |                   0.0 |                 0.0 |               0.0 |   12.0 |           0.0 |       6.452959 | 6.452959 |    0.850751 |   12.0 | 6.452959 |
    | 05.01. |           0.0 |         0.0 |   0.937172 |                   0.0 |                 0.0 |               0.0 |   10.0 |           0.0 |       8.999753 | 8.999753 |    0.937172 |   10.0 | 8.999753 |
    | 06.01. |           0.0 |         0.0 |   0.742131 |                   0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       8.257426 | 8.257426 |    0.742131 |    6.0 | 8.257426 |
    | 07.01. |           0.0 |         0.0 |   0.486374 |                   0.0 |                 0.0 |               0.0 |    3.0 |           0.0 |        5.96014 |  5.96014 |    0.486374 |    3.0 |  5.96014 |
    | 08.01. |           0.0 |         0.0 |   0.320717 |                   0.0 |                 0.0 |               0.0 |    2.0 |           0.0 |       3.917326 | 3.917326 |    0.320717 |    2.0 | 3.917326 |
    | 09.01. |           0.0 |         0.0 |   0.193041 |                   0.0 |                 0.0 |               0.0 |    1.0 |           0.0 |       2.477741 | 2.477741 |    0.193041 |    1.0 | 2.477741 |
    | 10.01. |           0.0 |         0.0 |   0.081262 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       1.293731 | 1.293731 |    0.081262 |    0.0 | 1.293731 |
    | 11.01. |           0.0 |         0.0 |   0.034208 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.544608 | 0.544608 |    0.034208 |    0.0 | 0.544608 |
    | 12.01. |           0.0 |         0.0 |   0.014537 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.227669 | 0.227669 |    0.014537 |    0.0 | 0.227669 |
    | 13.01. |           0.0 |         0.0 |   0.006178 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.096753 | 0.096753 |    0.006178 |    0.0 | 0.096753 |
    | 14.01. |           0.0 |         0.0 |   0.002482 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.042778 | 0.042778 |    0.002482 |    0.0 | 0.042778 |
    | 15.01. |           0.0 |         0.0 |   0.000997 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.017186 | 0.017186 |    0.000997 |    0.0 | 0.017186 |
    | 16.01. |           0.0 |         0.0 |   0.000508 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.005664 | 0.005664 |    0.000508 |    0.0 | 0.005664 |
    | 17.01. |           0.0 |         0.0 |   0.000259 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.002884 | 0.002884 |    0.000259 |    0.0 | 0.002884 |
    | 18.01. |           0.0 |         0.0 |   0.000132 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.001469 | 0.001469 |    0.000132 |    0.0 | 0.001469 |
    | 19.01. |           0.0 |         0.0 |   0.000067 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.000748 | 0.000748 |    0.000067 |    0.0 | 0.000748 |
    | 20.01. |           0.0 |         0.0 |   0.000034 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.000381 | 0.000381 |    0.000034 |    0.0 | 0.000381 |

There is no indication of an error in the water balance:

>>> from hydpy import round_
>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_v007_spillway:

spillway
________

Now, we introduce a more realistic relationship between flood discharge and stage based
on class |ANN|, where the spillway of the retention basin starts to become relevant
when the water volume exceeds about 1.4 million m³:

>>> waterlevel2flooddischarge(ANN(weights_input=10.0, weights_output=50.0,
...                               intercepts_hidden=-20.0, intercepts_output=0.0))
>>> figure = waterlevel2flooddischarge.plot(0.0, 2.0)
>>> from hydpy.core.testtools import save_autofig
>>> save_autofig("dam_v007_waterlevel2flooddischarge.png", figure=figure)

.. image:: dam_v007_waterlevel2flooddischarge.png
   :width: 400

The initially available storage volume of about 1.4 million m³ reduces the peak flow
to 7.3 m³/s:

.. integration-test::

    >>> test("dam_v007_spillway")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |          50.0 |         0.0 |     0.0864 |                   1.0 |                 0.0 |               0.0 |    0.0 |           0.0 |            0.0 |      0.0 |      0.0864 |    0.0 |      0.0 |
    | 03.01. |           0.0 |         0.0 |   0.604798 |                   0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       0.000022 | 0.000022 |    0.604798 |    6.0 | 0.000022 |
    | 04.01. |           0.0 |         0.0 |   1.630723 |                   0.0 |                 0.0 |               0.0 |   12.0 |           0.0 |       0.125869 | 0.125869 |    1.630723 |   12.0 | 0.125869 |
    | 05.01. |           0.0 |         0.0 |   1.860762 |                   0.0 |                 0.0 |               0.0 |   10.0 |           0.0 |       7.337517 | 7.337517 |    1.860762 |   10.0 | 7.337517 |
    | 06.01. |           0.0 |         0.0 |   1.801369 |                   0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       6.687413 | 6.687413 |    1.801369 |    6.0 | 6.687413 |
    | 07.01. |           0.0 |         0.0 |   1.729707 |                   0.0 |                 0.0 |               0.0 |    3.0 |           0.0 |       3.829425 | 3.829425 |    1.729707 |    3.0 | 3.829425 |
    | 08.01. |           0.0 |         0.0 |   1.689776 |                   0.0 |                 0.0 |               0.0 |    2.0 |           0.0 |       2.462161 | 2.462161 |    1.689776 |    2.0 | 2.462161 |
    | 09.01. |           0.0 |         0.0 |   1.637725 |                   0.0 |                 0.0 |               0.0 |    1.0 |           0.0 |       1.602443 | 1.602443 |    1.637725 |    1.0 | 1.602443 |
    | 10.01. |           0.0 |         0.0 |    1.56262 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.869271 | 0.869271 |     1.56262 |    0.0 | 0.869271 |
    | 11.01. |           0.0 |         0.0 |   1.519543 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.498579 | 0.498579 |    1.519543 |    0.0 | 0.498579 |
    | 12.01. |           0.0 |         0.0 |   1.489432 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.348504 | 0.348504 |    1.489432 |    0.0 | 0.348504 |
    | 13.01. |           0.0 |         0.0 |   1.466284 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.267917 | 0.267917 |    1.466284 |    0.0 | 0.267917 |
    | 14.01. |           0.0 |         0.0 |   1.447482 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.217618 | 0.217618 |    1.447482 |    0.0 | 0.217618 |
    | 15.01. |           0.0 |         0.0 |   1.431651 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.183225 | 0.183225 |    1.431651 |    0.0 | 0.183225 |
    | 16.01. |           0.0 |         0.0 |   1.417981 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.158219 | 0.158219 |    1.417981 |    0.0 | 0.158219 |
    | 17.01. |           0.0 |         0.0 |   1.405966 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.139064 | 0.139064 |    1.405966 |    0.0 | 0.139064 |
    | 18.01. |           0.0 |         0.0 |   1.395235 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.124197 | 0.124197 |    1.395235 |    0.0 | 0.124197 |
    | 19.01. |           0.0 |         0.0 |   1.385542 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.112196 | 0.112196 |    1.385542 |    0.0 | 0.112196 |
    | 20.01. |           0.0 |         0.0 |   1.376702 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.102307 | 0.102307 |    1.376702 |    0.0 | 0.102307 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_v007_allowed_release:

allowed release
_______________

In the :ref:`spillway example <dam_v007_spillway>`, |dam_v007| would not handle a second
event following the first one similarly well due to the retention basin not releasing
the remaining 1.4 million m³ water.  Setting the allowed release to 4 m³/s solves this
problem and decreases the amount of water stored during the beginning of the event and
thus further reduces the peak flow to 4.6 m³/s:

.. integration-test::

    >>> allowedrelease(4.0)
    >>> waterlevelminimumthreshold(0.1)
    >>> test("dam_v007_allowed_release")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |  -0.003204 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.037088 |            0.0 | 0.037088 |   -0.003204 |    0.0 | 0.037088 |
    | 02.01. |          50.0 |         0.0 |    0.06212 |                   1.0 |                 0.0 |               0.0 |    0.0 |       0.24393 |            0.0 |  0.24393 |     0.06212 |    0.0 |  0.24393 |
    | 03.01. |           0.0 |         0.0 |   0.277003 |                   0.0 |                 0.0 |               0.0 |    6.0 |      3.512924 |       0.000001 | 3.512925 |    0.277003 |    6.0 | 3.512925 |
    | 04.01. |           0.0 |         0.0 |   0.968183 |                   0.0 |                 0.0 |               0.0 |   12.0 |      3.999413 |       0.000827 | 4.000241 |    0.968183 |   12.0 | 4.000241 |
    | 05.01. |           0.0 |         0.0 |   1.481807 |                   0.0 |                 0.0 |               0.0 |   10.0 |           4.0 |        0.05527 |  4.05527 |    1.481807 |   10.0 |  4.05527 |
    | 06.01. |           0.0 |         0.0 |   1.605102 |                   0.0 |                 0.0 |               0.0 |    6.0 |           4.0 |       0.572981 | 4.572981 |    1.605102 |    6.0 | 4.572981 |
    | 07.01. |           0.0 |         0.0 |   1.474783 |                   0.0 |                 0.0 |               0.0 |    3.0 |           4.0 |       0.508315 | 4.508315 |    1.474783 |    3.0 | 4.508315 |
    | 08.01. |           0.0 |         0.0 |   1.291796 |                   0.0 |                 0.0 |               0.0 |    2.0 |           4.0 |       0.117913 | 4.117913 |    1.291796 |    2.0 | 4.117913 |
    | 09.01. |           0.0 |         0.0 |   1.031294 |                   0.0 |                 0.0 |               0.0 |    1.0 |           4.0 |       0.015063 | 4.015063 |    1.031294 |    1.0 | 4.015063 |
    | 10.01. |           0.0 |         0.0 |   0.685556 |                   0.0 |                 0.0 |               0.0 |    0.0 |           4.0 |       0.001601 | 4.001601 |    0.685556 |    0.0 | 4.001601 |
    | 11.01. |           0.0 |         0.0 |   0.339954 |                   0.0 |                 0.0 |               0.0 |    0.0 |      3.999967 |        0.00005 | 4.000018 |    0.339954 |    0.0 | 4.000018 |
    | 12.01. |           0.0 |         0.0 |   0.072368 |                   0.0 |                 0.0 |               0.0 |    0.0 |      3.097067 |       0.000001 | 3.097068 |    0.072368 |    0.0 | 3.097068 |
    | 13.01. |           0.0 |         0.0 |   0.037297 |                   0.0 |                 0.0 |               0.0 |    0.0 |       0.40591 |            0.0 |  0.40591 |    0.037297 |    0.0 |  0.40591 |
    | 14.01. |           0.0 |         0.0 |   0.023886 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.155222 |            0.0 | 0.155222 |    0.023886 |    0.0 | 0.155222 |
    | 15.01. |           0.0 |         0.0 |   0.015519 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.096838 |            0.0 | 0.096838 |    0.015519 |    0.0 | 0.096838 |
    | 16.01. |           0.0 |         0.0 |   0.009452 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.070215 |            0.0 | 0.070216 |    0.009452 |    0.0 | 0.070216 |
    | 17.01. |           0.0 |         0.0 |   0.004713 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.054858 |            0.0 | 0.054858 |    0.004713 |    0.0 | 0.054858 |
    | 18.01. |           0.0 |         0.0 |    0.00081 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.045172 |            0.0 | 0.045172 |     0.00081 |    0.0 | 0.045172 |
    | 19.01. |           0.0 |         0.0 |  -0.002506 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.038376 |            0.0 | 0.038376 |   -0.002506 |    0.0 | 0.038376 |
    | 20.01. |           0.0 |         0.0 |  -0.005387 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.033349 |            0.0 | 0.033349 |   -0.005387 |    0.0 | 0.033349 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

The initial and final water volumes shown in the last table are slightly negative,
which is due to the periods of zero inflow in combination with the value of parameter
|WaterLevelMinimumTolerance| set to 0.1 m.  One could avoid such negative values by
increasing parameter |WaterLevelMinimumThreshold| or decreasing parameter
|WaterLevelMinimumTolerance|.  Theoretically, one could set |WaterLevelMinimumTolerance|
to zero, but at the cost of potentially increased computation times.

.. _dam_v007_evaporation:

evaporation
___________

This example takes up the :ref:`evaporation example <dam_v006_evaporation>` of
application model |dam_v006|.  The effect of evaporation on the retention of the flood
wave is as little as to be expected:

.. integration-test::

    >>> inputs.evaporation.series = 10 * [1.0] + 10 * [5.0]
    >>> test("dam_v007_evaporation")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         1.0 |  -0.003504 |                   0.0 |               0.016 |             0.004 |    0.0 |      0.036559 |            0.0 | 0.036559 |   -0.003504 |    0.0 | 0.036559 |
    | 02.01. |          50.0 |         1.0 |   0.061087 |                   1.0 |              0.0192 |           0.01824 |    0.0 |      0.234179 |            0.0 | 0.234179 |    0.061087 |    0.0 | 0.234179 |
    | 03.01. |           0.0 |         1.0 |   0.275146 |                   0.0 |             0.01984 |           0.01984 |    6.0 |      3.502624 |       0.000001 | 3.502624 |    0.275146 |    6.0 | 3.502624 |
    | 04.01. |           0.0 |         1.0 |   0.964607 |                   0.0 |            0.019968 |          0.019968 |   12.0 |      3.999361 |       0.000798 | 4.000159 |    0.964607 |   12.0 | 4.000159 |
    | 05.01. |           0.0 |         1.0 |   1.476731 |                   0.0 |            0.019994 |          0.019994 |   10.0 |           4.0 |       0.052649 | 4.052649 |    1.476731 |   10.0 | 4.052649 |
    | 06.01. |           0.0 |         1.0 |   1.600633 |                   0.0 |            0.019999 |          0.019999 |    6.0 |           4.0 |       0.545947 | 4.545947 |    1.600633 |    6.0 | 4.545947 |
    | 07.01. |           0.0 |         1.0 |   1.470407 |                   0.0 |                0.02 |              0.02 |    3.0 |           4.0 |        0.48724 |  4.48724 |    1.470407 |    3.0 |  4.48724 |
    | 08.01. |           0.0 |         1.0 |   1.286164 |                   0.0 |                0.02 |              0.02 |    2.0 |           4.0 |       0.112447 | 4.112447 |    1.286164 |    2.0 | 4.112447 |
    | 09.01. |           0.0 |         1.0 |   1.024011 |                   0.0 |                0.02 |              0.02 |    1.0 |           4.0 |       0.014175 | 4.014175 |    1.024011 |    1.0 | 4.014175 |
    | 10.01. |           0.0 |         1.0 |   0.676555 |                   0.0 |                0.02 |              0.02 |    0.0 |           4.0 |       0.001488 | 4.001488 |    0.676555 |    0.0 | 4.001488 |
    | 11.01. |           0.0 |         5.0 |   0.323699 |                   0.0 |               0.084 |             0.084 |    0.0 |      3.999931 |       0.000046 | 3.999977 |    0.323699 |    0.0 | 3.999977 |
    | 12.01. |           0.0 |         5.0 |   0.065608 |                   0.0 |              0.0968 |            0.0968 |    0.0 |      2.890367 |       0.000001 | 2.890368 |    0.065608 |    0.0 | 2.890368 |
    | 13.01. |           0.0 |         5.0 |   0.029826 |                   0.0 |             0.09936 |           0.09936 |    0.0 |       0.31478 |            0.0 |  0.31478 |    0.029826 |    0.0 |  0.31478 |
    | 14.01. |           0.0 |         5.0 |   0.012324 |                   0.0 |            0.099872 |          0.099872 |    0.0 |      0.102704 |            0.0 | 0.102704 |    0.012324 |    0.0 | 0.102704 |
    | 15.01. |           0.0 |         5.0 |  -0.000279 |                   0.0 |            0.099974 |          0.093625 |    0.0 |      0.052242 |            0.0 | 0.052243 |   -0.000279 |    0.0 | 0.052243 |
    | 16.01. |           0.0 |         5.0 |  -0.003682 |                   0.0 |            0.099995 |          0.003615 |    0.0 |      0.035766 |            0.0 | 0.035766 |   -0.003682 |    0.0 | 0.035766 |
    | 17.01. |           0.0 |         5.0 |  -0.006422 |                   0.0 |            0.099999 |               0.0 |    0.0 |      0.031717 |            0.0 | 0.031717 |   -0.006422 |    0.0 | 0.031717 |
    | 18.01. |           0.0 |         5.0 |  -0.008859 |                   0.0 |                 0.1 |               0.0 |    0.0 |      0.028197 |            0.0 | 0.028197 |   -0.008859 |    0.0 | 0.028197 |
    | 19.01. |           0.0 |         5.0 |  -0.011051 |                   0.0 |                 0.1 |               0.0 |    0.0 |      0.025378 |            0.0 | 0.025378 |   -0.011051 |    0.0 | 0.025378 |
    | 20.01. |           0.0 |         5.0 |  -0.013044 |                   0.0 |                 0.1 |               0.0 |    0.0 |      0.023069 |            0.0 | 0.023069 |   -0.013044 |    0.0 | 0.023069 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...

# ...from HydPy
import hydpy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core.typingtools import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(modeltools.ELSModel):
    """Version 7 of HydPy-Dam."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (dam_model.Calc_AdjustedEvaporation_V1,)
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_ActualRelease_V2,
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

    def check_waterbalance(self, initial_conditions: ConditionsModel) -> float:
        r"""Determine the water balance error of the previous simulation run in million
        m³.

        Method |Model.check_waterbalance| calculates the balance error as follows:

        :math:`Seconds \cdot 10^{-6} \cdot \sum_{t=t0}^{t1}
        \big( AdjustedPrecipitation_t - ActualEvaporation_t + Inflow_t - Outflow_t \big)
        + \big( WaterVolume_{t0}^k - WaterVolume_{t1}^k \big)`

        The returned error should always be in scale with numerical precision so
        that it does not affect the simulation results in any relevant manner.

        Pick the required initial conditions before starting the simulation run via
        property |Sequences.conditions|.  See the integration tests of the application
        model |dam_v007| for some examples.
        """
        fluxes = self.sequences.fluxes
        first = initial_conditions["model"]["states"]
        last = self.sequences.states
        return (hydpy.pub.timegrids.stepsize.seconds / 1e6) * (
            sum(fluxes.adjustedprecipitation.series)
            - sum(fluxes.actualevaporation.series)
            + sum(fluxes.inflow.series)
            - sum(fluxes.outflow.series)
        ) - (last.watervolume - first["watervolume"])


tester = Tester()
cythonizer = Cythonizer()
