# pylint: disable=line-too-long, unused-wildcard-import
"""
.. _`LARSIM`: http://www.larsim.de/en/the-model/

|dam_lretention| is a simple "retention basin" model, similar to the "RUEC" model of
`LARSIM`_.  One can understand it as an extension of |dam_llake|, which partly requires
equal specifications.  Hence, before continuing, please first the documentation on
|dam_llake|.

In extension to |dam_llake|, |dam_lretention| implements the control parameter
|AllowedRelease| (and the related parameters |WaterLevelMinimumThreshold| and
|WaterLevelMinimumTolerance|).  Usually, one takes the discharge that does not cause
any harm downstream the "allowed release", making |dam_lretention| behave like a
retention basin without active control.  However, one can vary the allowed release
seasonally (|AllowedRelease| inherits from class |SeasonalParameter|).

In contrast to |dam_llake|, |dam_lretention| does not allow to restrict the speed of
the water level decrease during periods with little inflow, and thus does not use the
parameter |AllowedWaterLevelDrop|.

Integration tests
=================

.. how_to_understand_integration_tests::

We reuse the |dam_llake| test set, including identical input series and an identical
relationship between stage and volume:

>>> from hydpy import IntegrationTest, Element, pub
>>> pub.timegrids = "01.01.2000", "21.01.2000", "1d"
>>> from hydpy.models.dam_lretention import *
>>> parameterstep("1d")
>>> element = Element("element", inlets="input_", outlets="output")
>>> element.model = model
>>> test = IntegrationTest(element)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume
>>> test.inits = [(states.watervolume, 0.0), (logs.loggedadjustedevaporation, 0.0)]
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
>>> commission("1900-01-01")
>>> with model.add_precipmodel_v2("meteo_precip_io") as precipmodel:
...     precipitationfactor(1.0)
>>> precipmodel.prepare_inputseries()
>>> precipmodel.sequences.inputs.precipitation.series = [
...     0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> element.inlets.input_.sequences.sim.series = [
...     0.0, 0.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

.. _dam_lretention_base_scenario:

base scenario
_____________

To show that |dam_lretention| extends |dam_llake| correctly, we also define the same
quasi-linear relation between discharge and stage used throughout the integration tests
of |dam_llake| and additionally set the allowed release to 0 m³/s (which makes the
values of the two water-related control parameters irrelevant).  As expected,
|dam_lretention| now calculates outflow values identical to the ones of the
:ref:`dam_llake_base_scenario` example of |dam_llake| (where |AllowedWaterLevelDrop| is
|numpy.inf|):

.. integration-test::

    >>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 10.0]))
    >>> allowedrelease(0.0)
    >>> waterlevelminimumtolerance(0.1)
    >>> waterlevelminimumthreshold(0.0)
    >>> test("dam_lretention_base_scenario")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |   0.057853 |          50.0 |                   1.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |         0.3304 |   0.3304 |    0.057853 |    0.0 |   0.3304 |
    | 03.01. |     0.3715 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       2.369831 | 2.369831 |      0.3715 |    6.0 | 2.369831 |
    | 04.01. |    0.85081 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   12.0 |           0.0 |       6.452432 | 6.452432 |     0.85081 |   12.0 | 6.452432 |
    | 05.01. |    0.93712 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   10.0 |           0.0 |       9.001037 | 9.001037 |     0.93712 |   10.0 | 9.001037 |
    | 06.01. |   0.742087 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       8.257327 | 8.257327 |    0.742087 |    6.0 | 8.257327 |
    | 07.01. |   0.486328 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |           0.0 |       5.960176 | 5.960176 |    0.486328 |    3.0 | 5.960176 |
    | 08.01. |    0.32068 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |           0.0 |       3.917227 | 3.917227 |     0.32068 |    2.0 | 3.917227 |
    | 09.01. |   0.193011 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |           0.0 |       2.477651 | 2.477651 |    0.193011 |    1.0 | 2.477651 |
    | 10.01. |   0.081349 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       1.292382 | 1.292382 |    0.081349 |    0.0 | 1.292382 |
    | 11.01. |   0.034286 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.544712 | 0.544712 |    0.034286 |    0.0 | 0.544712 |
    | 12.01. |    0.01445 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.229577 | 0.229577 |     0.01445 |    0.0 | 0.229577 |
    | 13.01. |   0.006091 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.096747 | 0.096747 |    0.006091 |    0.0 | 0.096747 |
    | 14.01. |   0.002568 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.040782 | 0.040782 |    0.002568 |    0.0 | 0.040782 |
    | 15.01. |   0.001082 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.017191 | 0.017191 |    0.001082 |    0.0 | 0.017191 |
    | 16.01. |   0.000456 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.007254 | 0.007254 |    0.000456 |    0.0 | 0.007254 |
    | 17.01. |   0.000192 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.003054 | 0.003054 |    0.000192 |    0.0 | 0.003054 |
    | 18.01. |   0.000082 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.001277 | 0.001277 |    0.000082 |    0.0 | 0.001277 |
    | 19.01. |   0.000035 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.000542 | 0.000542 |    0.000035 |    0.0 | 0.000542 |
    | 20.01. |   0.000014 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |        0.00024 |  0.00024 |    0.000014 |    0.0 |  0.00024 |

There is no indication of an error in the water balance:

>>> from hydpy import round_
>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_lretention_spillway:

spillway
________

Now, we introduce a more realistic relationship between flood discharge and stage based
on class |ANN|, where the spillway of the retention basin starts to become relevant
when the water volume exceeds about 1.4 million m³:

>>> waterlevel2flooddischarge(ANN(weights_input=10.0, weights_output=50.0,
...                               intercepts_hidden=-20.0, intercepts_output=0.0))
>>> figure = waterlevel2flooddischarge.plot(0.0, 2.0)
>>> from hydpy.core.testtools import save_autofig
>>> save_autofig("dam_lretention_waterlevel2flooddischarge.png", figure=figure)

.. image:: dam_lretention_waterlevel2flooddischarge.png
   :width: 400

The initial storage volume of about 1.4 million m³ reduces the peak flow to 7.3 m³/s:

.. integration-test::

    >>> test("dam_lretention_spillway")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |     0.0864 |          50.0 |                   1.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |            0.0 |      0.0 |      0.0864 |    0.0 |      0.0 |
    | 03.01. |   0.604798 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       0.000022 | 0.000022 |    0.604798 |    6.0 | 0.000022 |
    | 04.01. |   1.630781 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   12.0 |           0.0 |       0.125198 | 0.125198 |    1.630781 |   12.0 | 0.125198 |
    | 05.01. |   1.860804 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   10.0 |           0.0 |       7.337699 | 7.337699 |    1.860804 |   10.0 | 7.337699 |
    | 06.01. |   1.801264 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |           0.0 |       6.689121 | 6.689121 |    1.801264 |    6.0 | 6.689121 |
    | 07.01. |   1.729848 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |           0.0 |       3.826574 | 3.826574 |    1.729848 |    3.0 | 3.826574 |
    | 08.01. |   1.689809 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |           0.0 |       2.463407 | 2.463407 |    1.689809 |    2.0 | 2.463407 |
    | 09.01. |    1.63782 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |           0.0 |       1.601733 | 1.601733 |     1.63782 |    1.0 | 1.601733 |
    | 10.01. |   1.561989 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.877667 | 0.877667 |    1.561989 |    0.0 | 0.877667 |
    | 11.01. |   1.519092 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.496492 | 0.496492 |    1.519092 |    0.0 | 0.496492 |
    | 12.01. |   1.489092 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.347228 | 0.347228 |    1.489092 |    0.0 | 0.347228 |
    | 13.01. |   1.466012 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.267126 | 0.267126 |    1.466012 |    0.0 | 0.267126 |
    | 14.01. |   1.447256 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.217087 | 0.217087 |    1.447256 |    0.0 | 0.217087 |
    | 15.01. |   1.431458 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.182846 | 0.182846 |    1.431458 |    0.0 | 0.182846 |
    | 16.01. |   1.417812 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.157936 | 0.157936 |    1.417812 |    0.0 | 0.157936 |
    | 17.01. |   1.405803 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.138999 | 0.138999 |    1.405803 |    0.0 | 0.138999 |
    | 18.01. |   1.395079 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.124117 | 0.124117 |    1.395079 |    0.0 | 0.124117 |
    | 19.01. |   1.385393 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.112112 | 0.112112 |    1.385393 |    0.0 | 0.112112 |
    | 20.01. |    1.37656 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           0.0 |       0.102224 | 0.102224 |     1.37656 |    0.0 | 0.102224 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_lretention_allowed_release:

allowed release
_______________

In the :ref:`spillway example <dam_lretention_spillway>`, |dam_lretention| would not
handle a second event following the first one similarly well due to the retention basin
not releasing the remaining 1.4 million m³ water.  Setting the allowed release to
4 m³/s solves this problem and decreases the amount of water stored during the
beginning of  the event and thus further reduces the peak flow to 4.6 m³/s:

.. integration-test::

    >>> allowedrelease(4.0)
    >>> waterlevelminimumthreshold(0.1)
    >>> test("dam_lretention_allowed_release")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   -0.00321 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.037149 |            0.0 | 0.037149 |    -0.00321 |    0.0 | 0.037149 |
    | 02.01. |   0.062185 |          50.0 |                   1.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.243112 |            0.0 | 0.243112 |    0.062185 |    0.0 | 0.243112 |
    | 03.01. |   0.276948 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |      3.514321 |       0.000001 | 3.514322 |    0.276948 |    6.0 | 3.514322 |
    | 04.01. |   0.968135 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   12.0 |      3.999902 |       0.000244 | 4.000146 |    0.968135 |   12.0 | 4.000146 |
    | 05.01. |   1.481783 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |   10.0 |           4.0 |          0.055 |    4.055 |    1.481783 |   10.0 |    4.055 |
    | 06.01. |   1.605037 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    6.0 |           4.0 |       0.573456 | 4.573456 |    1.605037 |    6.0 | 4.573456 |
    | 07.01. |   1.474747 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    3.0 |           4.0 |       0.507983 | 4.507983 |    1.474747 |    3.0 | 4.507983 |
    | 08.01. |   1.291755 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    2.0 |           4.0 |       0.117961 | 4.117961 |    1.291755 |    2.0 | 4.117961 |
    | 09.01. |   1.031269 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    1.0 |           4.0 |       0.014882 | 4.014882 |    1.031269 |    1.0 | 4.014882 |
    | 10.01. |   0.685594 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |           4.0 |        0.00087 |  4.00087 |    0.685594 |    0.0 |  4.00087 |
    | 11.01. |   0.339993 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      3.999968 |        0.00005 | 4.000018 |    0.339993 |    0.0 | 4.000018 |
    | 12.01. |   0.072257 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      3.098788 |       0.000001 | 3.098789 |    0.072257 |    0.0 | 3.098789 |
    | 13.01. |   0.037279 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |       0.40484 |            0.0 |  0.40484 |    0.037279 |    0.0 |  0.40484 |
    | 14.01. |   0.023832 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.155636 |            0.0 | 0.155637 |    0.023832 |    0.0 | 0.155637 |
    | 15.01. |   0.015478 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |       0.09669 |            0.0 | 0.096691 |    0.015478 |    0.0 | 0.096691 |
    | 16.01. |   0.009421 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.070111 |            0.0 | 0.070111 |    0.009421 |    0.0 | 0.070111 |
    | 17.01. |   0.004671 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.054974 |            0.0 | 0.054974 |    0.004671 |    0.0 | 0.054974 |
    | 18.01. |   0.000765 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.045201 |            0.0 | 0.045201 |    0.000765 |    0.0 | 0.045201 |
    | 19.01. |   -0.00255 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.038371 |            0.0 | 0.038371 |    -0.00255 |    0.0 | 0.038371 |
    | 20.01. |   -0.00543 |           0.0 |                   0.0 |                  0.0 |                 0.0 |               0.0 |    0.0 |      0.033331 |            0.0 | 0.033331 |    -0.00543 |    0.0 | 0.033331 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

The initial and final water volumes shown in the last table are slightly negative due
to the periods of zero inflow in combination with the value of parameter
|WaterLevelMinimumTolerance| set to 0.1 m.  One could avoid such negative values by
increasing |WaterLevelMinimumThreshold| or decreasing |WaterLevelMinimumTolerance|.
Theoretically, one could set |WaterLevelMinimumTolerance| to zero at the cost of
potentially increased computation times.

.. _dam_lretention_evaporation:

evaporation
___________

This example takes up the :ref:`evaporation example <dam_llake_evaporation>` of
application model |dam_llake|.  The effect of evaporation on the retention of the flood
wave is as little as expected:

.. integration-test::

    >>> with model.add_pemodel_v1("evap_ret_io") as pemodel:
    ...     evapotranspirationfactor(1.0)
    >>> pemodel.prepare_inputseries()
    >>> pemodel.sequences.inputs.referenceevapotranspiration.series = 10 * [1.0] + 10 * [5.0]
    >>> test("dam_lretention_evaporation")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  -0.003258 |           0.0 |                   0.0 |                  1.0 |               0.016 |          0.000638 |    0.0 |      0.037067 |            0.0 | 0.037067 |   -0.003258 |    0.0 | 0.037067 |
    | 02.01. |   0.061247 |          50.0 |                   1.0 |                  1.0 |              0.0192 |           0.01846 |    0.0 |      0.234962 |            0.0 | 0.234962 |    0.061247 |    0.0 | 0.234962 |
    | 03.01. |   0.275119 |           0.0 |                   0.0 |                  1.0 |             0.01984 |           0.01984 |    6.0 |      3.504788 |       0.000001 | 3.504789 |    0.275119 |    6.0 | 3.504789 |
    | 04.01. |   0.964579 |           0.0 |                   0.0 |                  1.0 |            0.019968 |          0.019968 |   12.0 |      3.999935 |       0.000231 | 4.000166 |    0.964579 |   12.0 | 4.000166 |
    | 05.01. |   1.476724 |           0.0 |                   0.0 |                  1.0 |            0.019994 |          0.019994 |   10.0 |           4.0 |       0.052405 | 4.052405 |    1.476724 |   10.0 | 4.052405 |
    | 06.01. |   1.600587 |           0.0 |                   0.0 |                  1.0 |            0.019999 |          0.019999 |    6.0 |           4.0 |       0.546402 | 4.546402 |    1.600587 |    6.0 | 4.546402 |
    | 07.01. |   1.470367 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 |    3.0 |           4.0 |       0.487174 | 4.487174 |    1.470367 |    3.0 | 4.487174 |
    | 08.01. |    1.28612 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 |    2.0 |           4.0 |       0.112486 | 4.112486 |     1.28612 |    2.0 | 4.112486 |
    | 09.01. |   1.023983 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 |    1.0 |           4.0 |       0.013999 | 4.013999 |    1.023983 |    1.0 | 4.013999 |
    | 10.01. |   0.676585 |           0.0 |                   0.0 |                  1.0 |                0.02 |              0.02 |    0.0 |           4.0 |       0.000805 | 4.000805 |    0.676585 |    0.0 | 4.000805 |
    | 11.01. |   0.323727 |           0.0 |                   0.0 |                  5.0 |               0.084 |             0.084 |    0.0 |      3.999977 |       0.000026 | 4.000003 |    0.323727 |    0.0 | 4.000003 |
    | 12.01. |   0.065961 |           0.0 |                   0.0 |                  5.0 |              0.0968 |            0.0968 |    0.0 |        2.8866 |       0.000001 | 2.886601 |    0.065961 |    0.0 | 2.886601 |
    | 13.01. |   0.029939 |           0.0 |                   0.0 |                  5.0 |             0.09936 |           0.09936 |    0.0 |      0.317568 |            0.0 | 0.317568 |    0.029939 |    0.0 | 0.317568 |
    | 14.01. |   0.012339 |           0.0 |                   0.0 |                  5.0 |            0.099872 |          0.099872 |    0.0 |      0.103835 |            0.0 | 0.103835 |    0.012339 |    0.0 | 0.103835 |
    | 15.01. |   -0.00034 |           0.0 |                   0.0 |                  5.0 |            0.099974 |          0.094506 |    0.0 |      0.052238 |            0.0 | 0.052238 |    -0.00034 |    0.0 | 0.052238 |
    | 16.01. |   -0.00358 |           0.0 |                   0.0 |                  5.0 |            0.099995 |          0.001014 |    0.0 |       0.03649 |            0.0 |  0.03649 |    -0.00358 |    0.0 |  0.03649 |
    | 17.01. |  -0.006336 |           0.0 |                   0.0 |                  5.0 |            0.099999 |               0.0 |    0.0 |      0.031894 |            0.0 | 0.031894 |   -0.006336 |    0.0 | 0.031894 |
    | 18.01. |  -0.008784 |           0.0 |                   0.0 |                  5.0 |                 0.1 |               0.0 |    0.0 |       0.02833 |            0.0 |  0.02833 |   -0.008784 |    0.0 |  0.02833 |
    | 19.01. |  -0.010985 |           0.0 |                   0.0 |                  5.0 |                 0.1 |               0.0 |    0.0 |       0.02548 |            0.0 |  0.02548 |   -0.010985 |    0.0 |  0.02548 |
    | 20.01. |  -0.012985 |           0.0 |                   0.0 |                  5.0 |                 0.1 |               0.0 |    0.0 |      0.023151 |            0.0 | 0.023151 |   -0.012985 |    0.0 | 0.023151 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_lretention_commissioning:

commissioning
_____________

This example extends the previous one with the commissioning mechanism shown and
discussed in the :ref:`analogue example <dam_llake_commissioning>` of application model
|dam_llake|:

.. integration-test::

    >>> commission("2000-01-04")
    >>> pemodel.sequences.inputs.referenceevapotranspiration.series = 50.0
    >>> test("dam_lretention_commissioning")
    |   date | waterlevel | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |        0.0 |           0.0 |                   0.0 |                 50.0 |                 0.8 |               0.0 |    0.0 |          0.04 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |        0.0 |          50.0 |                   1.0 |                 50.0 |                0.96 |              0.96 |    0.0 |          0.04 |            0.0 |     0.04 |         0.0 |    0.0 |     0.04 |
    | 03.01. |        0.0 |           0.0 |                   0.0 |                 50.0 |               0.992 |             0.992 |    6.0 |          0.04 |            0.0 |    5.008 |         0.0 |    6.0 |    5.008 |
    | 04.01. |   0.644932 |           0.0 |                   0.0 |                 50.0 |              0.9984 |          0.998224 |   12.0 |      3.537268 |       0.000016 | 3.537284 |    0.644932 |   12.0 | 3.537284 |
    | 05.01. |   1.076863 |           0.0 |                   0.0 |                 50.0 |             0.99968 |           0.99968 |   10.0 |           4.0 |       0.001121 | 4.001121 |    1.076863 |   10.0 | 4.001121 |
    | 06.01. |   1.162599 |           0.0 |                   0.0 |                 50.0 |            0.999936 |          0.999936 |    6.0 |           4.0 |       0.007751 | 4.007751 |    1.162599 |    6.0 | 4.007751 |
    | 07.01. |   0.989327 |           0.0 |                   0.0 |                 50.0 |            0.999987 |          0.999987 |    3.0 |           4.0 |       0.005478 | 4.005478 |    0.989327 |    3.0 | 4.005478 |
    | 08.01. |   0.730064 |           0.0 |                   0.0 |                 50.0 |            0.999997 |          0.999997 |    2.0 |           4.0 |       0.000728 | 4.000728 |    0.730064 |    2.0 | 4.000728 |
    | 09.01. |   0.384458 |           0.0 |                   0.0 |                 50.0 |            0.999999 |          0.999999 |    1.0 |      3.999996 |       0.000079 | 4.000075 |    0.384458 |    1.0 | 4.000075 |
    | 10.01. |   0.049401 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               1.0 |    0.0 |      2.877964 |       0.000001 | 2.877966 |    0.049401 |    0.0 | 2.877966 |
    | 11.01. |  -0.002303 |           0.0 |                   0.0 |                 50.0 |                 1.0 |          0.509487 |    0.0 |       0.08894 |            0.0 |  0.08894 |   -0.002303 |    0.0 |  0.08894 |
    | 12.01. |  -0.005213 |           0.0 |                   0.0 |                 50.0 |                 1.0 |          0.000004 |    0.0 |      0.033683 |            0.0 | 0.033684 |   -0.005213 |    0.0 | 0.033684 |
    | 13.01. |  -0.007782 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |      0.029734 |            0.0 | 0.029734 |   -0.007782 |    0.0 | 0.029734 |
    | 14.01. |  -0.010082 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |      0.026612 |            0.0 | 0.026612 |   -0.010082 |    0.0 | 0.026612 |
    | 15.01. |  -0.012162 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |      0.024081 |            0.0 | 0.024081 |   -0.012162 |    0.0 | 0.024081 |
    | 16.01. |  -0.014062 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |       0.02199 |            0.0 |  0.02199 |   -0.014062 |    0.0 |  0.02199 |
    | 17.01. |   -0.01581 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |      0.020232 |            0.0 | 0.020232 |    -0.01581 |    0.0 | 0.020232 |
    | 18.01. |  -0.017429 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |      0.018734 |            0.0 | 0.018734 |   -0.017429 |    0.0 | 0.018734 |
    | 19.01. |  -0.018936 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |      0.017442 |            0.0 | 0.017442 |   -0.018936 |    0.0 | 0.017442 |
    | 20.01. |  -0.020346 |           0.0 |                   0.0 |                 50.0 |                 1.0 |               0.0 |    0.0 |      0.016316 |            0.0 | 0.016316 |   -0.020346 |    0.0 | 0.016316 |

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(
    dam_model.ELSIEModel,
    dam_model.MixinSimpleWaterBalance,
    dam_model.Main_PrecipModel_V2,
    dam_model.Main_PEModel_V1,
):
    """|dam_lretention.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Dam-L-RB", description="retention basin model adopted from LARSIM"
    )
    __HYDPY_ROOTMODEL__ = True

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
        dam_solver.MaxEval,
        dam_solver.MaxCFL,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        dam_model.Calc_Precipitation_V1,
        dam_model.Calc_PotentialEvaporation_V1,
        dam_model.Calc_AdjustedEvaporation_V1,
    )
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pick_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualEvaporation_V3,
        dam_model.Calc_ActualRelease_V2,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_Outflow_V7,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V1,)
    OUTLET_METHODS = (dam_model.Calc_WaterLevel_V1, dam_model.Pass_Outflow_V1)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (precipinterfaces.PrecipModel_V2, petinterfaces.PETModel_V1)
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)


tester = Tester()
cythonizer = Cythonizer()
