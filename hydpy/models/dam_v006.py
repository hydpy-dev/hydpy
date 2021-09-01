# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Controlled lake version of HydPy-Dam.

.. _`LARSIM`: http://www.larsim.de/en/the-model/

Conceptionally, |dam_v006| is similar to the "controlled lake" model of `LARSIM`_
(selectable via the "SEEG" option) in its way to simulate flood retention processes.
However, in contrast to the "SEEG" option, it allows to directly include precipitation,
evaporation, and a (positive or negative) water exchange into the lake's water balance.

One can regard |dam_v006| as controlled in two ways.  First, it allows for seasonal
modifications of the rating curve via parameter |WaterLevel2FloodDischarge|; second, it
allows restricting the speed of the water level decrease during periods with little
inflow via parameter |AllowedWaterLevelDrop|.

|dam_v006| requires externally calculated values of potential evaporation, given via
the input sequence |Evaporation|.  If these reflect, for example, grass reference
evaporation, they usually show a too-high short-term variability.  Therefore, the
parameter |WeightEvaporation| provides a simple means to damp and delay the given
potential evaporation values by a simple time weighting approach.

The optional water exchange term enables bidirectional coupling of |dam_v006| instances
and other model objects.  Please see the documentation on the exchange model
|exch_v001|, where we demonstrate how to represent a system of two lakes connected by
a short ditch.

Like all models of the HydPy-D family, |dam_v006| solves its underlying continuous
ordinary differential equations with an error-adaptive numerical integration method.
Hence, simulation speed, robustness, and accuracy depend on the configuration of the
parameters of the model equations and the underlying solver.  We discuss these topics
in more detail in the documentation on the application model |dam_v001|.  Before the
first usage of any HydPy-Dam model, you should at least read how to set proper smoothing
parameter values and how to configure |InterpAlgorithm| objects for interpolating the
relationships between stage and volume (|WaterVolume2WaterLevel|) and between discharge
and stage (|WaterLevel2FloodDischarge|).

Integration tests
=================

.. how_to_understand_integration_tests::

We are going to perform all example calculations over 20 days:

>>> from hydpy import Element, Node, pub
>>> pub.timegrids = "01.01.2000", "21.01.2000", "1d"

Now, we prepare a |dam_v006| model instance in the usual manner:

>>> from hydpy.models.dam_v006 import *
>>> parameterstep("1d")

Next, we embed this model instance into an |Element|, being connected to one inlet
|Node| (`inflow`) and one outlet |Node| (`outflow`):

>>> inflow = Node("inflow", variable="Q")
>>> outflow = Node("outflow", variable="Q")
>>> exchange = Node("exchange", variable="E")
>>> lake = Element("lake", inlets=(inflow, exchange), outlets=outflow)
>>> lake.model = model

To execute the following examples conveniently, we prepare a test function object and
change some of its default output settings:

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(lake)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume

|WaterVolume| is the only state sequence of |dam_v006|.  The purpose of the only log
sequence |LoggedAdjustedEvaporation| is to allow for the mentioned time-weighting of
the external potential evaporation values.  We set the initial values of both sequences
to zero for each of the following examples:

>>> test.inits = [(states.watervolume, 0.0),
...               (logs.loggedadjustedevaporation, 0.0)]

To use method |Model.check_waterbalance| for proving that |dam_v006| keeps the water
balance in each example run requires storing the defined (initial) conditions before
performing the first simulation run:

>>> test.reset_inits()
>>> conditions = sequences.conditions

|dam_v006| assumes the relationship between |WaterLevel| and |WaterVolume| to be
constant over time.  For simplicity, we define a linear relationship by using |PPoly|:

>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
>>> figure = watervolume2waterlevel.plot(0.0, 1.0)
>>> from hydpy.core.testtools import save_autofig
>>> save_autofig("dam_v006_watervolume2waterlevel.png", figure=figure)

.. image:: dam_v006_watervolume2waterlevel.png
   :width: 400

|dam_v006| uses parameter |WaterLevel2FloodDischarge| (which extends parameter
|SeasonalInterpolator|) to allow for annual changes in the relationship between
|FloodDischarge| and |WaterLevel|.  Please read the documentation on class
|SeasonalInterpolator| on how to model seasonal patterns.  Here, we keep things as
simple as possible and define a single linear relationship that applies for the whole
year:

>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 10.0]))
>>> figure = waterlevel2flooddischarge.plot(0.0, 1.0)
>>> figure = save_autofig("dam_v006_waterlevel2flooddischarge.png", figure=figure)

.. image:: dam_v006_waterlevel2flooddischarge.png
   :width: 400

The following group of parameters deal with lake precipitation and evaporation.  Note
that, despite |dam_v006|'s ability to calculate the water-level dependent surface area
(see aide sequence |dam_aides.SurfaceArea|), it always assumes a fixed surface area
(defined by control parameter |dam_control.SurfaceArea|) for converting precipitation
and evaporation heights into volumes.  Here, we set this fixed surface area to 1.44 km²:

>>> surfacearea(1.44)

We set the correction factors for precipitation and evaporation both to 1.2:

>>> correctionprecipitation(1.2)
>>> correctionevaporation(1.2)

Given the daily simulation time step, we configure moderate damping and delay of the
external evaporation values (0.8 is relatively close to 1.0, which would avoid any
delay and damping, while 0.0 would result in a complete loss of variability):

>>> weightevaporation(0.8)

|dam_v006| uses the parameter |ThresholdEvaporation| for defining the water level
around which actual evaporation switches from zero to potential evaporation.  As usual
but not mandatory, we set this threshold to 0 m:

>>> thresholdevaporation(0.0)

Additionally, we set the values of the related smoothing parameters |DischargeTolerance|
and |ToleranceEvaporation| to 0.1 m³/s and 1 mm (these are values we can recommend
for many cases -- see the documentation on application model |dam_v001| on how to
fine-tune such smoothing parameters to your needs):

>>> dischargetolerance(0.1)
>>> toleranceevaporation(0.001)

Finally, we define a precipitation series including only a heavy one-day rainfall event
and a corresponding inflowing flood wave, starting and ending with zero discharge:

>>> inputs.precipitation.series = [
...     0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> lake.inlets.inflow.sequences.sim.series = [
...     0.0, 0.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

.. _dam_v006_base_scenario:

base scenario
_____________

For our first example, we set the allowed water level drop to |numpy.inf| and the
external potential evaporation as well as the exchange values to zero to ensure they do
not affect the calculated lake outflow:

>>> allowedwaterleveldrop(inf)
>>> inputs.evaporation.series = 0.0
>>> exchange.sequences.sim.series = 0.0

The only purpose of parameter |CatchmentArea| is to determine reasonable default values
for the parameter |AbsErrorMax| automatically, controlling the accuracy of the numerical
integration process:

>>> catchmentarea(86.4)
>>> from hydpy import round_
>>> round_(solver.abserrormax.INIT)
0.01
>>> parameters.update()
>>> solver.abserrormax
abserrormax(0.01)

The following test results show the expected storage retention pattern.  The sums of
inflow and outflow are nearly identical, and the maximum of the outflow graph intersects
with the falling limb of the inflow graph:

.. integration-test::

    >>> test("dam_v006_base_scenario")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | exchange | flooddischarge |  outflow | watervolume | exchange | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |            0.0 |      0.0 |         0.0 |      0.0 |    0.0 |      0.0 |
    | 02.01. |          50.0 |         0.0 |   0.057904 |                   1.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.329814 | 0.329814 |    0.057904 |      0.0 |    0.0 | 0.329814 |
    | 03.01. |           0.0 |         0.0 |   0.371486 |                   0.0 |                 0.0 |               0.0 |    6.0 |      0.0 |       2.370574 | 2.370574 |    0.371486 |      0.0 |    6.0 | 2.370574 |
    | 04.01. |           0.0 |         0.0 |   0.850751 |                   0.0 |                 0.0 |               0.0 |   12.0 |      0.0 |       6.452959 | 6.452959 |    0.850751 |      0.0 |   12.0 | 6.452959 |
    | 05.01. |           0.0 |         0.0 |   0.937172 |                   0.0 |                 0.0 |               0.0 |   10.0 |      0.0 |       8.999753 | 8.999753 |    0.937172 |      0.0 |   10.0 | 8.999753 |
    | 06.01. |           0.0 |         0.0 |   0.742131 |                   0.0 |                 0.0 |               0.0 |    6.0 |      0.0 |       8.257426 | 8.257426 |    0.742131 |      0.0 |    6.0 | 8.257426 |
    | 07.01. |           0.0 |         0.0 |   0.486374 |                   0.0 |                 0.0 |               0.0 |    3.0 |      0.0 |        5.96014 |  5.96014 |    0.486374 |      0.0 |    3.0 |  5.96014 |
    | 08.01. |           0.0 |         0.0 |   0.320717 |                   0.0 |                 0.0 |               0.0 |    2.0 |      0.0 |       3.917326 | 3.917326 |    0.320717 |      0.0 |    2.0 | 3.917326 |
    | 09.01. |           0.0 |         0.0 |   0.193041 |                   0.0 |                 0.0 |               0.0 |    1.0 |      0.0 |       2.477741 | 2.477741 |    0.193041 |      0.0 |    1.0 | 2.477741 |
    | 10.01. |           0.0 |         0.0 |   0.081262 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       1.293731 | 1.293731 |    0.081262 |      0.0 |    0.0 | 1.293731 |
    | 11.01. |           0.0 |         0.0 |   0.034208 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.544608 | 0.544608 |    0.034208 |      0.0 |    0.0 | 0.544608 |
    | 12.01. |           0.0 |         0.0 |   0.014537 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.227669 | 0.227669 |    0.014537 |      0.0 |    0.0 | 0.227669 |
    | 13.01. |           0.0 |         0.0 |   0.006178 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.096753 | 0.096753 |    0.006178 |      0.0 |    0.0 | 0.096753 |
    | 14.01. |           0.0 |         0.0 |   0.002482 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.042778 | 0.042778 |    0.002482 |      0.0 |    0.0 | 0.042778 |
    | 15.01. |           0.0 |         0.0 |   0.000997 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.017186 | 0.017186 |    0.000997 |      0.0 |    0.0 | 0.017186 |
    | 16.01. |           0.0 |         0.0 |   0.000508 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.005664 | 0.005664 |    0.000508 |      0.0 |    0.0 | 0.005664 |
    | 17.01. |           0.0 |         0.0 |   0.000259 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.002884 | 0.002884 |    0.000259 |      0.0 |    0.0 | 0.002884 |
    | 18.01. |           0.0 |         0.0 |   0.000132 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.001469 | 0.001469 |    0.000132 |      0.0 |    0.0 | 0.001469 |
    | 19.01. |           0.0 |         0.0 |   0.000067 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.000748 | 0.000748 |    0.000067 |      0.0 |    0.0 | 0.000748 |
    | 20.01. |           0.0 |         0.0 |   0.000034 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.000381 | 0.000381 |    0.000034 |      0.0 |    0.0 | 0.000381 |

|dam_v006| achieves this sufficiently high accuracy with 174 calls to
its underlying system of differential equations, which averages to less
than nine calls per day:

>>> model.numvars.nmb_calls
174

There is no indication of an error in the water balance:

>>> from hydpy import round_
>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_v006_low_accuracy:

low accuracy
____________

By increasing the numerical tolerance, e.g. setting |AbsErrorMax| to 0.1 m³/s, we gain
some additional speedups without relevant deteriorations of the results (|dam_v006|
usually achieves higher accuracies than indicated by the actual tolerance value):

.. integration-test::

    >>> model.numvars.nmb_calls = 0
    >>> solver.abserrormax(0.1)
    >>> test("dam_v006_low_accuracy")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | exchange | flooddischarge |  outflow | watervolume | exchange | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |            0.0 |      0.0 |         0.0 |      0.0 |    0.0 |      0.0 |
    | 02.01. |          50.0 |         0.0 |   0.057503 |                   1.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.334458 | 0.334458 |    0.057503 |      0.0 |    0.0 | 0.334458 |
    | 03.01. |           0.0 |         0.0 |   0.371631 |                   0.0 |                 0.0 |               0.0 |    6.0 |      0.0 |        2.36426 |  2.36426 |    0.371631 |      0.0 |    6.0 |  2.36426 |
    | 04.01. |           0.0 |         0.0 |    0.85129 |                   0.0 |                 0.0 |               0.0 |   12.0 |      0.0 |       6.448386 | 6.448386 |     0.85129 |      0.0 |   12.0 | 6.448386 |
    | 05.01. |           0.0 |         0.0 |   0.936803 |                   0.0 |                 0.0 |               0.0 |   10.0 |      0.0 |       9.010274 | 9.010274 |    0.936803 |      0.0 |   10.0 | 9.010274 |
    | 06.01. |           0.0 |         0.0 |   0.743132 |                   0.0 |                 0.0 |               0.0 |    6.0 |      0.0 |       8.241563 | 8.241563 |    0.743132 |      0.0 |    6.0 | 8.241563 |
    | 07.01. |           0.0 |         0.0 |    0.48654 |                   0.0 |                 0.0 |               0.0 |    3.0 |      0.0 |       5.969805 | 5.969805 |     0.48654 |      0.0 |    3.0 | 5.969805 |
    | 08.01. |           0.0 |         0.0 |   0.321772 |                   0.0 |                 0.0 |               0.0 |    2.0 |      0.0 |       3.907047 | 3.907047 |    0.321772 |      0.0 |    2.0 | 3.907047 |
    | 09.01. |           0.0 |         0.0 |   0.194247 |                   0.0 |                 0.0 |               0.0 |    1.0 |      0.0 |       2.475983 | 2.475983 |    0.194247 |      0.0 |    1.0 | 2.475983 |
    | 10.01. |           0.0 |         0.0 |   0.082549 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       1.292793 | 1.292793 |    0.082549 |      0.0 |    0.0 | 1.292793 |
    | 11.01. |           0.0 |         0.0 |   0.035081 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |         0.5494 |   0.5494 |    0.035081 |      0.0 |    0.0 |   0.5494 |
    | 12.01. |           0.0 |         0.0 |   0.014094 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.242907 | 0.242907 |    0.014094 |      0.0 |    0.0 | 0.242907 |
    | 13.01. |           0.0 |         0.0 |   0.007177 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.080053 | 0.080053 |    0.007177 |      0.0 |    0.0 | 0.080053 |
    | 14.01. |           0.0 |         0.0 |   0.003655 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.040767 | 0.040767 |    0.003655 |      0.0 |    0.0 | 0.040767 |
    | 15.01. |           0.0 |         0.0 |   0.001861 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.020761 | 0.020761 |    0.001861 |      0.0 |    0.0 | 0.020761 |
    | 16.01. |           0.0 |         0.0 |   0.000948 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.010572 | 0.010572 |    0.000948 |      0.0 |    0.0 | 0.010572 |
    | 17.01. |           0.0 |         0.0 |   0.000483 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.005384 | 0.005384 |    0.000483 |      0.0 |    0.0 | 0.005384 |
    | 18.01. |           0.0 |         0.0 |   0.000246 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.002742 | 0.002742 |    0.000246 |      0.0 |    0.0 | 0.002742 |
    | 19.01. |           0.0 |         0.0 |   0.000125 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.001396 | 0.001396 |    0.000125 |      0.0 |    0.0 | 0.001396 |
    | 20.01. |           0.0 |         0.0 |   0.000064 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.000711 | 0.000711 |    0.000064 |      0.0 |    0.0 | 0.000711 |

>>> model.numvars.nmb_calls
104

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_v006_water_level_drop:

water level drop
________________

When setting |AllowedWaterLevelDrop| to 0.1 m/d, the resulting outflow hydrograph shows
a plateau in its falling limb.  This plateau is in the period where little inflow
occurs, but the potential outflow (|FloodDischarge|) is still high due to large amounts
of stored water.  In agreement with the linear relationship between the water volume
and the water level, there is a constant decrease in the water volume when the allowed
water level drop limits the outflow:

.. integration-test::

    >>> allowedwaterleveldrop(0.1)
    >>> solver.abserrormax(0.01)
    >>> test("dam_v006_water_level_drop")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | exchange | flooddischarge |  outflow | watervolume | exchange | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |            0.0 |      0.0 |         0.0 |      0.0 |    0.0 |      0.0 |
    | 02.01. |          50.0 |         0.0 |   0.057904 |                   1.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.329814 | 0.329814 |    0.057904 |      0.0 |    0.0 | 0.329814 |
    | 03.01. |           0.0 |         0.0 |   0.371486 |                   0.0 |                 0.0 |               0.0 |    6.0 |      0.0 |       2.370574 | 2.370574 |    0.371486 |      0.0 |    6.0 | 2.370574 |
    | 04.01. |           0.0 |         0.0 |   0.850751 |                   0.0 |                 0.0 |               0.0 |   12.0 |      0.0 |       6.452959 | 6.452959 |    0.850751 |      0.0 |   12.0 | 6.452959 |
    | 05.01. |           0.0 |         0.0 |   0.937172 |                   0.0 |                 0.0 |               0.0 |   10.0 |      0.0 |       8.999753 | 8.999753 |    0.937172 |      0.0 |   10.0 | 8.999753 |
    | 06.01. |           0.0 |         0.0 |   0.837314 |                   0.0 |                 0.0 |               0.0 |    6.0 |      0.0 |        8.87243 | 7.155768 |    0.837314 |      0.0 |    6.0 | 7.155768 |
    | 07.01. |           0.0 |         0.0 |   0.737455 |                   0.0 |                 0.0 |               0.0 |    3.0 |      0.0 |       7.873846 | 4.155768 |    0.737455 |      0.0 |    3.0 | 4.155768 |
    | 08.01. |           0.0 |         0.0 |   0.637597 |                   0.0 |                 0.0 |               0.0 |    2.0 |      0.0 |       6.875262 | 3.155768 |    0.637597 |      0.0 |    2.0 | 3.155768 |
    | 09.01. |           0.0 |         0.0 |   0.537739 |                   0.0 |                 0.0 |               0.0 |    1.0 |      0.0 |       5.876679 | 2.155768 |    0.537739 |      0.0 |    1.0 | 2.155768 |
    | 10.01. |           0.0 |         0.0 |    0.43788 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       4.878095 | 1.155768 |     0.43788 |      0.0 |    0.0 | 1.155768 |
    | 11.01. |           0.0 |         0.0 |   0.338022 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       3.879512 | 1.155768 |    0.338022 |      0.0 |    0.0 | 1.155768 |
    | 12.01. |           0.0 |         0.0 |   0.238164 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       2.880928 | 1.155768 |    0.238164 |      0.0 |    0.0 | 1.155768 |
    | 13.01. |           0.0 |         0.0 |   0.138316 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       1.882449 | 1.155647 |    0.138316 |      0.0 |    0.0 | 1.155647 |
    | 14.01. |           0.0 |         0.0 |   0.059782 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.940746 | 0.908959 |    0.059782 |      0.0 |    0.0 | 0.908959 |
    | 15.01. |           0.0 |         0.0 |   0.025166 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.400649 | 0.400648 |    0.025166 |      0.0 |    0.0 | 0.400648 |
    | 16.01. |           0.0 |         0.0 |   0.010695 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.167488 | 0.167488 |    0.010695 |      0.0 |    0.0 | 0.167488 |
    | 17.01. |           0.0 |         0.0 |   0.004545 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.071178 | 0.071178 |    0.004545 |      0.0 |    0.0 | 0.071178 |
    | 18.01. |           0.0 |         0.0 |   0.001826 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |        0.03147 |  0.03147 |    0.001826 |      0.0 |    0.0 |  0.03147 |
    | 19.01. |           0.0 |         0.0 |    0.00093 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.010371 | 0.010371 |     0.00093 |      0.0 |    0.0 | 0.010371 |
    | 20.01. |           0.0 |         0.0 |   0.000474 |                   0.0 |                 0.0 |               0.0 |    0.0 |      0.0 |       0.005282 | 0.005282 |    0.000474 |      0.0 |    0.0 | 0.005282 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_v006_evaporation:

evaporation
___________

In this example, we set the (unadjusted) potential evaporation to 1 mm/d for the first
ten days and 5 mm/d for the last ten days.  The adjusted evaporation follows the given
potential evaporation with a short delay.  When the water volume reaches zero, actual
evaporation is nearly but, due to the defined smoothing, not completely zero.  Hence,
slightly negative water volumes result (which do not cause negative outflow):

.. integration-test::

    >>> inputs.evaporation.series = 10 * [1.0] + 10 * [5.0]
    >>> test("dam_v006_evaporation")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | exchange | flooddischarge |  outflow | watervolume | exchange | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         1.0 |  -0.000373 |                   0.0 |               0.016 |          0.004321 |    0.0 |      0.0 |      -0.003456 |      0.0 |   -0.000373 |      0.0 |    0.0 |      0.0 |
    | 02.01. |          50.0 |         1.0 |   0.056654 |                   1.0 |              0.0192 |          0.018386 |    0.0 |      0.0 |       0.321392 | 0.321579 |    0.056654 |      0.0 |    0.0 | 0.321579 |
    | 03.01. |           0.0 |         1.0 |   0.369812 |                   0.0 |             0.01984 |           0.01984 |    6.0 |      0.0 |       2.355646 | 2.355646 |    0.369812 |      0.0 |    6.0 | 2.355646 |
    | 04.01. |           0.0 |         1.0 |    0.84889 |                   0.0 |            0.019968 |          0.019968 |   12.0 |      0.0 |       6.435147 | 6.435147 |     0.84889 |      0.0 |   12.0 | 6.435147 |
    | 05.01. |           0.0 |         1.0 |   0.935231 |                   0.0 |            0.019994 |          0.019994 |   10.0 |      0.0 |       8.980686 | 8.980686 |    0.935231 |      0.0 |   10.0 | 8.980686 |
    | 06.01. |           0.0 |         1.0 |   0.835373 |                   0.0 |            0.019999 |          0.019999 |    6.0 |      0.0 |       8.853018 | 7.135769 |    0.835373 |      0.0 |    6.0 | 7.135769 |
    | 07.01. |           0.0 |         1.0 |   0.735514 |                   0.0 |                0.02 |              0.02 |    3.0 |      0.0 |       7.854435 | 4.135768 |    0.735514 |      0.0 |    3.0 | 4.135768 |
    | 08.01. |           0.0 |         1.0 |   0.635656 |                   0.0 |                0.02 |              0.02 |    2.0 |      0.0 |       6.855851 | 3.135768 |    0.635656 |      0.0 |    2.0 | 3.135768 |
    | 09.01. |           0.0 |         1.0 |   0.535798 |                   0.0 |                0.02 |              0.02 |    1.0 |      0.0 |       5.857267 | 2.135768 |    0.535798 |      0.0 |    1.0 | 2.135768 |
    | 10.01. |           0.0 |         1.0 |   0.435939 |                   0.0 |                0.02 |              0.02 |    0.0 |      0.0 |       4.858684 | 1.135768 |    0.435939 |      0.0 |    0.0 | 1.135768 |
    | 11.01. |           0.0 |         5.0 |   0.336081 |                   0.0 |               0.084 |             0.084 |    0.0 |      0.0 |         3.8601 | 1.071768 |    0.336081 |      0.0 |    0.0 | 1.071768 |
    | 12.01. |           0.0 |         5.0 |   0.236222 |                   0.0 |              0.0968 |            0.0968 |    0.0 |      0.0 |       2.861517 | 1.058968 |    0.236222 |      0.0 |    0.0 | 1.058968 |
    | 13.01. |           0.0 |         5.0 |   0.136367 |                   0.0 |             0.09936 |           0.09936 |    0.0 |      0.0 |       1.862958 | 1.056379 |    0.136367 |      0.0 |    0.0 | 1.056379 |
    | 14.01. |           0.0 |         5.0 |    0.05408 |                   0.0 |            0.099872 |          0.099872 |    0.0 |      0.0 |       0.906509 | 0.852516 |     0.05408 |      0.0 |    0.0 | 0.852516 |
    | 15.01. |           0.0 |         5.0 |   0.016936 |                   0.0 |            0.099974 |          0.099974 |    0.0 |      0.0 |       0.329933 | 0.329932 |    0.016936 |      0.0 |    0.0 | 0.329932 |
    | 16.01. |           0.0 |         5.0 |   0.001323 |                   0.0 |            0.099995 |          0.099992 |    0.0 |      0.0 |       0.080723 | 0.080723 |    0.001323 |      0.0 |    0.0 | 0.080723 |
    | 17.01. |           0.0 |         5.0 |  -0.000756 |                   0.0 |            0.099999 |          0.022768 |    0.0 |      0.0 |      -0.004582 | 0.001295 |   -0.000756 |      0.0 |    0.0 | 0.001295 |
    | 18.01. |           0.0 |         5.0 |  -0.000926 |                   0.0 |                 0.1 |          0.001966 |    0.0 |      0.0 |       -0.00886 |      0.0 |   -0.000926 |      0.0 |    0.0 |      0.0 |
    | 19.01. |           0.0 |         5.0 |  -0.001022 |                   0.0 |                 0.1 |          0.001102 |    0.0 |      0.0 |      -0.009866 |      0.0 |   -0.001022 |      0.0 |    0.0 |      0.0 |
    | 20.01. |           0.0 |         5.0 |  -0.001088 |                   0.0 |                 0.1 |          0.000771 |    0.0 |      0.0 |      -0.010607 |      0.0 |   -0.001088 |      0.0 |    0.0 |      0.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_v006_exchange:

exchange
________

The water exchange functionality of |dam_v006| is optional insofar that one does not
need to connect the inlet sequence |E| to any nodes.  If there is a connection to one
or multiple nodes, they can add and subtract water, indicated by positive or negative
values.  This mechanism allows establishing bidirectional water exchange between
different |dam_v006| (see the documentation |exch_v001| for further information).

|dam_v006| handles the water exchange strictly as input, meaning it always includes it
into its water balance without any modification.  Hence, other models calculating the
water exchange must ensure that it does not bring |dam_v006| into an unrealistic state.
For demonstration, we set the water exchange to 0.5 m³/s in the first half of the
simulation period and -0.5 m³/s in the second half, which causes highly negative water
volumes at the end of the simulation period:

.. integration-test::

    >>> exchange.sequences.sim.series = 10 * [0.5] + 10 * [-0.5]
    >>> test("dam_v006_exchange")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | exchange | flooddischarge |  outflow | watervolume | exchange | inflow |  outflow |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         1.0 |   0.028037 |                   0.0 |               0.016 |            0.0156 |    0.0 |      0.5 |       0.159893 | 0.159893 |    0.028037 |      0.5 |    0.0 | 0.159893 |
    | 02.01. |          50.0 |         1.0 |   0.097547 |                   1.0 |              0.0192 |            0.0192 |    0.0 |      0.5 |       0.676291 | 0.676291 |    0.097547 |      0.5 |    0.0 | 0.676291 |
    | 03.01. |           0.0 |         1.0 |   0.415973 |                   0.0 |             0.01984 |           0.01984 |    6.0 |      0.5 |       2.794675 | 2.794675 |    0.415973 |      0.5 |    6.0 | 2.794675 |
    | 04.01. |           0.0 |         1.0 |   0.897272 |                   0.0 |            0.019968 |          0.019968 |   12.0 |      0.5 |       6.909446 | 6.909446 |    0.897272 |      0.5 |   12.0 | 6.909446 |
    | 05.01. |           0.0 |         1.0 |    0.98455 |                   0.0 |            0.019994 |          0.019994 |   10.0 |      0.5 |       9.469841 | 9.469841 |     0.98455 |      0.5 |   10.0 | 9.469841 |
    | 06.01. |           0.0 |         1.0 |   0.884691 |                   0.0 |            0.019999 |          0.019999 |    6.0 |      0.5 |       9.346206 | 7.635769 |    0.884691 |      0.5 |    6.0 | 7.635769 |
    | 07.01. |           0.0 |         1.0 |   0.784833 |                   0.0 |                0.02 |              0.02 |    3.0 |      0.5 |       8.347623 | 4.635768 |    0.784833 |      0.5 |    3.0 | 4.635768 |
    | 08.01. |           0.0 |         1.0 |   0.684975 |                   0.0 |                0.02 |              0.02 |    2.0 |      0.5 |       7.349039 | 3.635768 |    0.684975 |      0.5 |    2.0 | 3.635768 |
    | 09.01. |           0.0 |         1.0 |   0.585116 |                   0.0 |                0.02 |              0.02 |    1.0 |      0.5 |       6.350455 | 2.635768 |    0.585116 |      0.5 |    1.0 | 2.635768 |
    | 10.01. |           0.0 |         1.0 |   0.485258 |                   0.0 |                0.02 |              0.02 |    0.0 |      0.5 |       5.351872 | 1.635768 |    0.485258 |      0.5 |    0.0 | 1.635768 |
    | 11.01. |           0.0 |         5.0 |     0.3854 |                   0.0 |               0.084 |             0.084 |    0.0 |     -0.5 |       4.353288 | 0.571768 |      0.3854 |     -0.5 |    0.0 | 0.571768 |
    | 12.01. |           0.0 |         5.0 |   0.285541 |                   0.0 |              0.0968 |            0.0968 |    0.0 |     -0.5 |       3.354705 | 0.558968 |    0.285541 |     -0.5 |    0.0 | 0.558968 |
    | 13.01. |           0.0 |         5.0 |   0.185683 |                   0.0 |             0.09936 |           0.09936 |    0.0 |     -0.5 |       2.356121 | 0.556408 |    0.185683 |     -0.5 |    0.0 | 0.556408 |
    | 14.01. |           0.0 |         5.0 |   0.085827 |                   0.0 |            0.099872 |          0.099872 |    0.0 |     -0.5 |       1.357564 | 0.555865 |    0.085827 |     -0.5 |    0.0 | 0.555865 |
    | 15.01. |           0.0 |         5.0 |   0.003815 |                   0.0 |            0.099974 |          0.099974 |    0.0 |     -0.5 |       0.401743 | 0.349246 |    0.003815 |     -0.5 |    0.0 | 0.349246 |
    | 16.01. |           0.0 |         5.0 |  -0.039982 |                   0.0 |            0.099995 |             0.005 |    0.0 |     -0.5 |        -0.1878 | 0.001907 |   -0.039982 |     -0.5 |    0.0 | 0.001907 |
    | 17.01. |           0.0 |         5.0 |  -0.083182 |                   0.0 |            0.099999 |               0.0 |    0.0 |     -0.5 |      -0.615821 |      0.0 |   -0.083182 |     -0.5 |    0.0 |      0.0 |
    | 18.01. |           0.0 |         5.0 |  -0.126382 |                   0.0 |                 0.1 |               0.0 |    0.0 |     -0.5 |      -1.047821 |      0.0 |   -0.126382 |     -0.5 |    0.0 |      0.0 |
    | 19.01. |           0.0 |         5.0 |  -0.169582 |                   0.0 |                 0.1 |               0.0 |    0.0 |     -0.5 |      -1.479821 |      0.0 |   -0.169582 |     -0.5 |    0.0 |      0.0 |
    | 20.01. |           0.0 |         5.0 |  -0.212782 |                   0.0 |                 0.1 |               0.0 |    0.0 |     -0.5 |      -1.911821 |      0.0 |   -0.212782 |     -0.5 |    0.0 |      0.0 |

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from standard library
from typing import *

# ...from HydPy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
import hydpy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core.typingtools import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(modeltools.ELSModel):
    """Version 6 of HydPy-Dam."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (dam_model.Calc_AdjustedEvaporation_V1,)
    RECEIVER_METHODS = ()
    ADD_METHODS = (dam_model.Fix_Min1_V1,)
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V1,
        dam_model.Pic_Exchange_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_SurfaceArea_V1,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_AllowedDischarge_V1,
        dam_model.Calc_Outflow_V2,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V4,)
    OUTLET_METHODS = (
        dam_model.Calc_WaterLevel_V1,
        dam_model.Pass_Outflow_V1,
    )
    SENDER_METHODS = ()
    SUBMODELS = ()

    def check_waterbalance(
        self,
        initial_conditions: Dict[str, Dict[str, ArrayFloat]],
    ) -> float:
        r"""Determine the water balance error of the previous simulation run in million
        m³.

        Method |Model.check_waterbalance| calculates the balance error as follows:

        :math:`Seconds \cdot 10^{-6} \cdot \sum_{t=t0}^{t1}
        \big( AdjustedPrecipitation_t - ActualEvaporation_t +
        Inflow_t - Outflow_t + Exchange_t \big)
        + \big( WaterVolume_{t0}^k - WaterVolume_{t1}^k \big)`

        The returned error should always be in scale with numerical precision so
        that it does not affect the simulation results in any relevant manner.

        Pick the required initial conditions before starting the simulation run via
        property |Sequences.conditions|.  See the integration tests of the application
        model |dam_v006| for some examples.
        """
        fluxes = self.sequences.fluxes
        first = initial_conditions["states"]
        last = self.sequences.states
        return (hydpy.pub.timegrids.stepsize.seconds / 1e6) * (
            sum(fluxes.adjustedprecipitation.series)
            - sum(fluxes.actualevaporation.series)
            + sum(fluxes.inflow.series)
            - sum(fluxes.outflow.series)
            + sum(fluxes.exchange.series)
        ) - (last.watervolume - first["watervolume"])


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
