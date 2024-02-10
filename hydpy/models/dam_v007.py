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
    | 02.01. |          50.0 |         0.0 |   0.057853 |                   1.0 |                 0.0 |               0.0 |    0.0 |           0.0 |         0.3304 |   0.3304 |    0.057853 |    0.0 |   0.3304 |
    | 03.01. |           0.0 |         0.0 |     0.3715 |                   0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       2.369831 | 2.369831 |      0.3715 |    6.0 | 2.369831 |
    | 04.01. |           0.0 |         0.0 |    0.85081 |                   0.0 |                 0.0 |               0.0 |   12.0 |           0.0 |       6.452432 | 6.452432 |     0.85081 |   12.0 | 6.452432 |
    | 05.01. |           0.0 |         0.0 |    0.93712 |                   0.0 |                 0.0 |               0.0 |   10.0 |           0.0 |       9.001037 | 9.001037 |     0.93712 |   10.0 | 9.001037 |
    | 06.01. |           0.0 |         0.0 |   0.742087 |                   0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       8.257327 | 8.257327 |    0.742087 |    6.0 | 8.257327 |
    | 07.01. |           0.0 |         0.0 |   0.486328 |                   0.0 |                 0.0 |               0.0 |    3.0 |           0.0 |       5.960176 | 5.960176 |    0.486328 |    3.0 | 5.960176 |
    | 08.01. |           0.0 |         0.0 |    0.32068 |                   0.0 |                 0.0 |               0.0 |    2.0 |           0.0 |       3.917227 | 3.917227 |     0.32068 |    2.0 | 3.917227 |
    | 09.01. |           0.0 |         0.0 |   0.193011 |                   0.0 |                 0.0 |               0.0 |    1.0 |           0.0 |       2.477651 | 2.477651 |    0.193011 |    1.0 | 2.477651 |
    | 10.01. |           0.0 |         0.0 |   0.081349 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       1.292382 | 1.292382 |    0.081349 |    0.0 | 1.292382 |
    | 11.01. |           0.0 |         0.0 |   0.034286 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.544712 | 0.544712 |    0.034286 |    0.0 | 0.544712 |
    | 12.01. |           0.0 |         0.0 |    0.01445 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.229577 | 0.229577 |     0.01445 |    0.0 | 0.229577 |
    | 13.01. |           0.0 |         0.0 |   0.006091 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.096747 | 0.096747 |    0.006091 |    0.0 | 0.096747 |
    | 14.01. |           0.0 |         0.0 |   0.002568 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.040782 | 0.040782 |    0.002568 |    0.0 | 0.040782 |
    | 15.01. |           0.0 |         0.0 |   0.001082 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.017191 | 0.017191 |    0.001082 |    0.0 | 0.017191 |
    | 16.01. |           0.0 |         0.0 |   0.000456 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.007254 | 0.007254 |    0.000456 |    0.0 | 0.007254 |
    | 17.01. |           0.0 |         0.0 |   0.000192 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.003054 | 0.003054 |    0.000192 |    0.0 | 0.003054 |
    | 18.01. |           0.0 |         0.0 |   0.000082 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.001277 | 0.001277 |    0.000082 |    0.0 | 0.001277 |
    | 19.01. |           0.0 |         0.0 |   0.000035 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.000542 | 0.000542 |    0.000035 |    0.0 | 0.000542 |
    | 20.01. |           0.0 |         0.0 |   0.000014 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |        0.00024 |  0.00024 |    0.000014 |    0.0 |  0.00024 |

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
    | 04.01. |           0.0 |         0.0 |   1.630781 |                   0.0 |                 0.0 |               0.0 |   12.0 |           0.0 |       0.125198 | 0.125198 |    1.630781 |   12.0 | 0.125198 |
    | 05.01. |           0.0 |         0.0 |   1.860804 |                   0.0 |                 0.0 |               0.0 |   10.0 |           0.0 |       7.337699 | 7.337699 |    1.860804 |   10.0 | 7.337699 |
    | 06.01. |           0.0 |         0.0 |   1.801264 |                   0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       6.689121 | 6.689121 |    1.801264 |    6.0 | 6.689121 |
    | 07.01. |           0.0 |         0.0 |   1.729848 |                   0.0 |                 0.0 |               0.0 |    3.0 |           0.0 |       3.826574 | 3.826574 |    1.729848 |    3.0 | 3.826574 |
    | 08.01. |           0.0 |         0.0 |   1.689809 |                   0.0 |                 0.0 |               0.0 |    2.0 |           0.0 |       2.463407 | 2.463407 |    1.689809 |    2.0 | 2.463407 |
    | 09.01. |           0.0 |         0.0 |    1.63782 |                   0.0 |                 0.0 |               0.0 |    1.0 |           0.0 |       1.601733 | 1.601733 |     1.63782 |    1.0 | 1.601733 |
    | 10.01. |           0.0 |         0.0 |   1.561989 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.877667 | 0.877667 |    1.561989 |    0.0 | 0.877667 |
    | 11.01. |           0.0 |         0.0 |   1.519092 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.496492 | 0.496492 |    1.519092 |    0.0 | 0.496492 |
    | 12.01. |           0.0 |         0.0 |   1.489092 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.347228 | 0.347228 |    1.489092 |    0.0 | 0.347228 |
    | 13.01. |           0.0 |         0.0 |   1.466012 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.267126 | 0.267126 |    1.466012 |    0.0 | 0.267126 |
    | 14.01. |           0.0 |         0.0 |   1.447256 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.217087 | 0.217087 |    1.447256 |    0.0 | 0.217087 |
    | 15.01. |           0.0 |         0.0 |   1.431458 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.182846 | 0.182846 |    1.431458 |    0.0 | 0.182846 |
    | 16.01. |           0.0 |         0.0 |   1.417812 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.157936 | 0.157936 |    1.417812 |    0.0 | 0.157936 |
    | 17.01. |           0.0 |         0.0 |   1.405803 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.138999 | 0.138999 |    1.405803 |    0.0 | 0.138999 |
    | 18.01. |           0.0 |         0.0 |   1.395079 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.124117 | 0.124117 |    1.395079 |    0.0 | 0.124117 |
    | 19.01. |           0.0 |         0.0 |   1.385393 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.112112 | 0.112112 |    1.385393 |    0.0 | 0.112112 |
    | 20.01. |           0.0 |         0.0 |    1.37656 |                   0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.102224 | 0.102224 |     1.37656 |    0.0 | 0.102224 |

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
    | 01.01. |           0.0 |         0.0 |   -0.00321 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.037149 |            0.0 | 0.037149 |    -0.00321 |    0.0 | 0.037149 |
    | 02.01. |          50.0 |         0.0 |   0.062185 |                   1.0 |                 0.0 |               0.0 |    0.0 |      0.243112 |            0.0 | 0.243112 |    0.062185 |    0.0 | 0.243112 |
    | 03.01. |           0.0 |         0.0 |   0.276948 |                   0.0 |                 0.0 |               0.0 |    6.0 |      3.514321 |       0.000001 | 3.514322 |    0.276948 |    6.0 | 3.514322 |
    | 04.01. |           0.0 |         0.0 |   0.968135 |                   0.0 |                 0.0 |               0.0 |   12.0 |      3.999902 |       0.000244 | 4.000146 |    0.968135 |   12.0 | 4.000146 |
    | 05.01. |           0.0 |         0.0 |   1.481783 |                   0.0 |                 0.0 |               0.0 |   10.0 |           4.0 |          0.055 |    4.055 |    1.481783 |   10.0 |    4.055 |
    | 06.01. |           0.0 |         0.0 |   1.605037 |                   0.0 |                 0.0 |               0.0 |    6.0 |           4.0 |       0.573456 | 4.573456 |    1.605037 |    6.0 | 4.573456 |
    | 07.01. |           0.0 |         0.0 |   1.474747 |                   0.0 |                 0.0 |               0.0 |    3.0 |           4.0 |       0.507983 | 4.507983 |    1.474747 |    3.0 | 4.507983 |
    | 08.01. |           0.0 |         0.0 |   1.291755 |                   0.0 |                 0.0 |               0.0 |    2.0 |           4.0 |       0.117961 | 4.117961 |    1.291755 |    2.0 | 4.117961 |
    | 09.01. |           0.0 |         0.0 |   1.031269 |                   0.0 |                 0.0 |               0.0 |    1.0 |           4.0 |       0.014882 | 4.014882 |    1.031269 |    1.0 | 4.014882 |
    | 10.01. |           0.0 |         0.0 |   0.685594 |                   0.0 |                 0.0 |               0.0 |    0.0 |           4.0 |        0.00087 |  4.00087 |    0.685594 |    0.0 |  4.00087 |
    | 11.01. |           0.0 |         0.0 |   0.339993 |                   0.0 |                 0.0 |               0.0 |    0.0 |      3.999968 |        0.00005 | 4.000018 |    0.339993 |    0.0 | 4.000018 |
    | 12.01. |           0.0 |         0.0 |   0.072257 |                   0.0 |                 0.0 |               0.0 |    0.0 |      3.098788 |       0.000001 | 3.098789 |    0.072257 |    0.0 | 3.098789 |
    | 13.01. |           0.0 |         0.0 |   0.037279 |                   0.0 |                 0.0 |               0.0 |    0.0 |       0.40484 |            0.0 |  0.40484 |    0.037279 |    0.0 |  0.40484 |
    | 14.01. |           0.0 |         0.0 |   0.023832 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.155636 |            0.0 | 0.155637 |    0.023832 |    0.0 | 0.155637 |
    | 15.01. |           0.0 |         0.0 |   0.015478 |                   0.0 |                 0.0 |               0.0 |    0.0 |       0.09669 |            0.0 | 0.096691 |    0.015478 |    0.0 | 0.096691 |
    | 16.01. |           0.0 |         0.0 |   0.009421 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.070111 |            0.0 | 0.070111 |    0.009421 |    0.0 | 0.070111 |
    | 17.01. |           0.0 |         0.0 |   0.004671 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.054974 |            0.0 | 0.054974 |    0.004671 |    0.0 | 0.054974 |
    | 18.01. |           0.0 |         0.0 |   0.000765 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.045201 |            0.0 | 0.045201 |    0.000765 |    0.0 | 0.045201 |
    | 19.01. |           0.0 |         0.0 |   -0.00255 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.038371 |            0.0 | 0.038371 |    -0.00255 |    0.0 | 0.038371 |
    | 20.01. |           0.0 |         0.0 |   -0.00543 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.033331 |            0.0 | 0.033331 |    -0.00543 |    0.0 | 0.033331 |

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
    | 01.01. |           0.0 |         1.0 |  -0.003258 |                   0.0 |               0.016 |          0.000638 |    0.0 |      0.037067 |            0.0 | 0.037067 |   -0.003258 |    0.0 | 0.037067 |
    | 02.01. |          50.0 |         1.0 |   0.061247 |                   1.0 |              0.0192 |           0.01846 |    0.0 |      0.234962 |            0.0 | 0.234962 |    0.061247 |    0.0 | 0.234962 |
    | 03.01. |           0.0 |         1.0 |   0.275119 |                   0.0 |             0.01984 |           0.01984 |    6.0 |      3.504788 |       0.000001 | 3.504789 |    0.275119 |    6.0 | 3.504789 |
    | 04.01. |           0.0 |         1.0 |   0.964579 |                   0.0 |            0.019968 |          0.019968 |   12.0 |      3.999935 |       0.000231 | 4.000166 |    0.964579 |   12.0 | 4.000166 |
    | 05.01. |           0.0 |         1.0 |   1.476724 |                   0.0 |            0.019994 |          0.019994 |   10.0 |           4.0 |       0.052405 | 4.052405 |    1.476724 |   10.0 | 4.052405 |
    | 06.01. |           0.0 |         1.0 |   1.600587 |                   0.0 |            0.019999 |          0.019999 |    6.0 |           4.0 |       0.546402 | 4.546402 |    1.600587 |    6.0 | 4.546402 |
    | 07.01. |           0.0 |         1.0 |   1.470367 |                   0.0 |                0.02 |              0.02 |    3.0 |           4.0 |       0.487174 | 4.487174 |    1.470367 |    3.0 | 4.487174 |
    | 08.01. |           0.0 |         1.0 |    1.28612 |                   0.0 |                0.02 |              0.02 |    2.0 |           4.0 |       0.112486 | 4.112486 |     1.28612 |    2.0 | 4.112486 |
    | 09.01. |           0.0 |         1.0 |   1.023983 |                   0.0 |                0.02 |              0.02 |    1.0 |           4.0 |       0.013999 | 4.013999 |    1.023983 |    1.0 | 4.013999 |
    | 10.01. |           0.0 |         1.0 |   0.676585 |                   0.0 |                0.02 |              0.02 |    0.0 |           4.0 |       0.000805 | 4.000805 |    0.676585 |    0.0 | 4.000805 |
    | 11.01. |           0.0 |         5.0 |   0.323727 |                   0.0 |               0.084 |             0.084 |    0.0 |      3.999977 |       0.000026 | 4.000003 |    0.323727 |    0.0 | 4.000003 |
    | 12.01. |           0.0 |         5.0 |   0.065961 |                   0.0 |              0.0968 |            0.0968 |    0.0 |        2.8866 |       0.000001 | 2.886601 |    0.065961 |    0.0 | 2.886601 |
    | 13.01. |           0.0 |         5.0 |   0.029939 |                   0.0 |             0.09936 |           0.09936 |    0.0 |      0.317568 |            0.0 | 0.317568 |    0.029939 |    0.0 | 0.317568 |
    | 14.01. |           0.0 |         5.0 |   0.012339 |                   0.0 |            0.099872 |          0.099872 |    0.0 |      0.103835 |            0.0 | 0.103835 |    0.012339 |    0.0 | 0.103835 |
    | 15.01. |           0.0 |         5.0 |   -0.00034 |                   0.0 |            0.099974 |          0.094506 |    0.0 |      0.052238 |            0.0 | 0.052238 |    -0.00034 |    0.0 | 0.052238 |
    | 16.01. |           0.0 |         5.0 |   -0.00358 |                   0.0 |            0.099995 |          0.001014 |    0.0 |       0.03649 |            0.0 |  0.03649 |    -0.00358 |    0.0 |  0.03649 |
    | 17.01. |           0.0 |         5.0 |  -0.006336 |                   0.0 |            0.099999 |               0.0 |    0.0 |      0.031894 |            0.0 | 0.031894 |   -0.006336 |    0.0 | 0.031894 |
    | 18.01. |           0.0 |         5.0 |  -0.008784 |                   0.0 |                 0.1 |               0.0 |    0.0 |       0.02833 |            0.0 |  0.02833 |   -0.008784 |    0.0 |  0.02833 |
    | 19.01. |           0.0 |         5.0 |  -0.010985 |                   0.0 |                 0.1 |               0.0 |    0.0 |       0.02548 |            0.0 |  0.02548 |   -0.010985 |    0.0 |  0.02548 |
    | 20.01. |           0.0 |         5.0 |  -0.012985 |                   0.0 |                 0.1 |               0.0 |    0.0 |      0.023151 |            0.0 | 0.023151 |   -0.012985 |    0.0 | 0.023151 |

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
    OUTLET_METHODS = (dam_model.Calc_WaterLevel_V1, dam_model.Pass_Outflow_V1)
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
