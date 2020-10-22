# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Controlled lake version of HydPy-Dam.

.. _`LARSIM`: http://www.larsim.de/en/the-model/

Conceptionally, |dam_v006| is similar to the "controlled lake" model of
`LARSIM`_ (selectable via the "SEEG" option).  It simulates flood retention
processes only and neglects losses due to evaporation.

One can regard |dam_v006| as controlled in two ways.  First, it allows
for seasonal modifications of the rating curve via parameter
|WaterLevel2FloodDischarge|; second, it allows to restrict the speed of
the water level decrease during periods with little inflow via parameter
|AllowedWaterLevelDrop|.

Like all models of the HydPy-D family, |dam_v006| solves its underlying
continuous ordinary differential equations with an error-adaptive numerical
integration method.  Hence, simulation speed, robustness, and accuracy
depend both on the configuration of the parameters of the model equations
and the underlying solver.  We discuss these topics in more detail in the
documentation on the application model |dam_v001|.  Before the first usage
of any HydPy-Dam model, you should at least read how to set proper
smoothing parameter values and how to configure the artificial neural
networks used to model the relationships between stage and volume
(|WaterVolume2WaterLevel|) and between discharge and stage
(|WaterLevel2FloodDischarge|).

Integration tests
=================

.. how_to_understand_integration_tests::

We are going to perform all example calculations over 20 days:

>>> from hydpy import pub
>>> pub.timegrids = '01.01.2000', '21.01.2000', '1d'

Now, we prepare a |dam_v006| model instance in the usual manner:

>>> from hydpy.models.dam_v006 import *
>>> parameterstep('1d')

Next, we embed this model instance into an |Element|, being connected
to one inlet |Node| (`input_`) and one outlet |Node| (`output`):

>>> from hydpy import Element
>>> element = Element('element', inlets='input_', outlets='output')
>>> element.model = model

To execute the following examples conveniently, we prepare a test function
object and change some of its default output settings:

>>> from hydpy import IntegrationTest
>>> IntegrationTest.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> IntegrationTest.plotting_options.axis2 = states.watervolume
>>> test = IntegrationTest(element)
>>> test.dateformat = '%d.%m.'

|WaterVolume| is the only state sequence of |dam_v006|.  We set its initial
value for each example to zero:

>>> test.inits = [(states.watervolume, 0.0)]

|dam_v006| assumes the relationship between |WaterLevel| and |WaterVolume|
to be constant over time.  To allow for maximum flexibility, it uses
parameter |WaterVolume2WaterLevel|, which extends the artificial neural
network parameter |anntools.ANN|.  For simplicity, we enforce a linear
relationship between |WaterLevel| and |WaterVolume| (as shown in the
following graph):

>>> watervolume2waterlevel(
...     weights_input=1.0, weights_output=1.0,
...     intercepts_hidden=0.0, intercepts_output=0.0,
...     activation=0)
>>> watervolume2waterlevel.plot(0.0, 1.0)

.. testsetup::

    >>> import os
    >>> from matplotlib import pyplot
    >>> from hydpy.docs import figs
    >>> pyplot.savefig(
    ...     os.path.join(
    ...         figs.__path__[0],
    ...         'dam_v006_watervolume2waterlevel.png',
    ...     ),
    ... )
    >>> pyplot.close()

.. image:: dam_v006_watervolume2waterlevel.png
   :width: 400

|dam_v006| uses parameter |WaterLevel2FloodDischarge| (which extends
parameter |anntools.SeasonalANN|) to allow for annual changes in the
relationship between |FloodDischarge| and |WaterLevel|.  Please read the
documentation on class |anntools.SeasonalANN| on how to model seasonal
patterns.  Here, we again keep things as simple as possible and define
a single linear relationship which applies for the whole year:

>>> waterlevel2flooddischarge(ann(
...     weights_input=1.0, weights_output=10.0,
...     intercepts_hidden=0.0, intercepts_output=0.0,
...     activation=0))
>>> waterlevel2flooddischarge.plot(0.0, 1.0)

.. testsetup::

    >>> pyplot.savefig(
    ...     os.path.join(
    ...         figs.__path__[0],
    ...         'dam_v006_waterlevel2flooddischarge.png',
    ...     ),
    ... )
    >>> pyplot.close()

.. image:: dam_v006_waterlevel2flooddischarge.png
   :width: 400

Additionally, we set the value of the related smoothing parameter
|DischargeTolerance| to 0.1 m³/s (this is a value we can recommend
for many cases -- see the documentation on application model |dam_v001|
on how to fine-tune such smoothing parameter to your needs):

>>> dischargetolerance(0.1)

Finally, we define the ingoing flood wave, starting and ending with zero
discharge:

>>> element.inlets.input_.sequences.sim.series = [
...     0.0, 1.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

.. _dam_v006_base_scenario:

base scenario
_____________

For our first example, we set the |AllowedWaterLevelDrop| to |numpy.inf|,
to make sure this possible restriction does never affect the calculated
lake outflow:

>>> allowedwaterleveldrop(inf)

The only purpose of parameter |CatchmentArea| is to determine reasonable
default values for the parameter |AbsErrorMax| automatically, controlling
the accuracy of the numerical integration process:

>>> catchmentarea(86.4)
>>> from hydpy import round_
>>> round_(solver.abserrormax.INIT)
0.01
>>> parameters.update()
>>> solver.abserrormax
abserrormax(0.01)

The following test results show the expected storage retention pattern.
The sums of inflow and outflow are nearly identical, and the maximum of
the outflow graph intersects with the falling limb of the inflow graph:

.. integration-test::

    >>> test('dam_v006_base_scenario')
    |   date | inflow | flooddischarge |  outflow | watervolume | input_ |   output |
    ---------------------------------------------------------------------------------
    | 01.01. |    0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |       0.329814 | 0.329814 |    0.057904 |    1.0 | 0.329814 |
    | 03.01. |    6.0 |       2.370574 | 2.370574 |    0.371486 |    6.0 | 2.370574 |
    | 04.01. |   12.0 |       6.452959 | 6.452959 |    0.850751 |   12.0 | 6.452959 |
    | 05.01. |   10.0 |       8.999753 | 8.999753 |    0.937172 |   10.0 | 8.999753 |
    | 06.01. |    6.0 |       8.257426 | 8.257426 |    0.742131 |    6.0 | 8.257426 |
    | 07.01. |    3.0 |        5.96014 |  5.96014 |    0.486374 |    3.0 |  5.96014 |
    | 08.01. |    2.0 |       3.917326 | 3.917326 |    0.320717 |    2.0 | 3.917326 |
    | 09.01. |    1.0 |       2.477741 | 2.477741 |    0.193041 |    1.0 | 2.477741 |
    | 10.01. |    0.0 |       1.293731 | 1.293731 |    0.081262 |    0.0 | 1.293731 |
    | 11.01. |    0.0 |       0.544608 | 0.544608 |    0.034208 |    0.0 | 0.544608 |
    | 12.01. |    0.0 |       0.227669 | 0.227669 |    0.014537 |    0.0 | 0.227669 |
    | 13.01. |    0.0 |       0.096753 | 0.096753 |    0.006178 |    0.0 | 0.096753 |
    | 14.01. |    0.0 |       0.042778 | 0.042778 |    0.002482 |    0.0 | 0.042778 |
    | 15.01. |    0.0 |       0.017186 | 0.017186 |    0.000997 |    0.0 | 0.017186 |
    | 16.01. |    0.0 |       0.005664 | 0.005664 |    0.000508 |    0.0 | 0.005664 |
    | 17.01. |    0.0 |       0.002884 | 0.002884 |    0.000259 |    0.0 | 0.002884 |
    | 18.01. |    0.0 |       0.001469 | 0.001469 |    0.000132 |    0.0 | 0.001469 |
    | 19.01. |    0.0 |       0.000748 | 0.000748 |    0.000067 |    0.0 | 0.000748 |
    | 20.01. |    0.0 |       0.000381 | 0.000381 |    0.000034 |    0.0 | 0.000381 |

|dam_v006| achieves this sufficiently high accuracy with 174 calls to
its underlying system of differential equations, which averages to less
than nine calls per day:

>>> model.numvars.nmb_calls
174

.. _dam_v006_low_accuracy:

low accuracy
____________

Through increasing the numerical tolerance, e.g. setting |AbsErrorMax|
to 0.1 m³/s, we can gain some additional speedups without relevant
deteriorations of the results (|dam_v006| usually achieves higher
accuracies than indicated by the actual tolerance value):

.. integration-test::

    >>> model.numvars.nmb_calls = 0
    >>> solver.abserrormax(0.1)
    >>> test('dam_v006_low_accuracy')
    |   date | inflow | flooddischarge |  outflow | watervolume | input_ |   output |
    ---------------------------------------------------------------------------------
    | 01.01. |    0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |       0.334458 | 0.334458 |    0.057503 |    1.0 | 0.334458 |
    | 03.01. |    6.0 |        2.36426 |  2.36426 |    0.371631 |    6.0 |  2.36426 |
    | 04.01. |   12.0 |       6.448386 | 6.448386 |     0.85129 |   12.0 | 6.448386 |
    | 05.01. |   10.0 |       9.010274 | 9.010274 |    0.936803 |   10.0 | 9.010274 |
    | 06.01. |    6.0 |       8.241563 | 8.241563 |    0.743132 |    6.0 | 8.241563 |
    | 07.01. |    3.0 |       5.969805 | 5.969805 |     0.48654 |    3.0 | 5.969805 |
    | 08.01. |    2.0 |       3.907047 | 3.907047 |    0.321772 |    2.0 | 3.907047 |
    | 09.01. |    1.0 |       2.475983 | 2.475983 |    0.194247 |    1.0 | 2.475983 |
    | 10.01. |    0.0 |       1.292793 | 1.292793 |    0.082549 |    0.0 | 1.292793 |
    | 11.01. |    0.0 |         0.5494 |   0.5494 |    0.035081 |    0.0 |   0.5494 |
    | 12.01. |    0.0 |       0.242907 | 0.242907 |    0.014094 |    0.0 | 0.242907 |
    | 13.01. |    0.0 |       0.080053 | 0.080053 |    0.007177 |    0.0 | 0.080053 |
    | 14.01. |    0.0 |       0.040767 | 0.040767 |    0.003655 |    0.0 | 0.040767 |
    | 15.01. |    0.0 |       0.020761 | 0.020761 |    0.001861 |    0.0 | 0.020761 |
    | 16.01. |    0.0 |       0.010572 | 0.010572 |    0.000948 |    0.0 | 0.010572 |
    | 17.01. |    0.0 |       0.005384 | 0.005384 |    0.000483 |    0.0 | 0.005384 |
    | 18.01. |    0.0 |       0.002742 | 0.002742 |    0.000246 |    0.0 | 0.002742 |
    | 19.01. |    0.0 |       0.001396 | 0.001396 |    0.000125 |    0.0 | 0.001396 |
    | 20.01. |    0.0 |       0.000711 | 0.000711 |    0.000064 |    0.0 | 0.000711 |

>>> model.numvars.nmb_calls
104

.. _dam_v006_water_level_drop:

water level drop
________________

When setting |AllowedWaterLevelDrop| to 0.1 m/d, the resulting outflow
hydrograph shows a plateau in its falling limb.  This plateau is placed in
the period where little inflow occurs, but the potential outflow
(|FloodDischarge|) is still high due to large amounts of stored water:

.. integration-test::

    >>> allowedwaterleveldrop(0.1)
    >>> solver.abserrormax(0.01)
    >>> test('dam_v006_water_level_drop')
    |   date | inflow | flooddischarge |  outflow | watervolume | input_ |   output |
    ---------------------------------------------------------------------------------
    | 01.01. |    0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |       0.329814 | 0.329814 |    0.057904 |    1.0 | 0.329814 |
    | 03.01. |    6.0 |       2.370574 | 2.370574 |    0.371486 |    6.0 | 2.370574 |
    | 04.01. |   12.0 |       6.452959 | 6.452959 |    0.850751 |   12.0 | 6.452959 |
    | 05.01. |   10.0 |       8.999753 | 8.999753 |    0.937172 |   10.0 | 8.999753 |
    | 06.01. |    6.0 |        8.87243 | 7.155768 |    0.837314 |    6.0 | 7.155768 |
    | 07.01. |    3.0 |       7.873846 | 4.155768 |    0.737455 |    3.0 | 4.155768 |
    | 08.01. |    2.0 |       6.875262 | 3.155768 |    0.637597 |    2.0 | 3.155768 |
    | 09.01. |    1.0 |       5.876679 | 2.155768 |    0.537739 |    1.0 | 2.155768 |
    | 10.01. |    0.0 |       4.878095 | 1.155768 |     0.43788 |    0.0 | 1.155768 |
    | 11.01. |    0.0 |       3.879512 | 1.155768 |    0.338022 |    0.0 | 1.155768 |
    | 12.01. |    0.0 |       2.880928 | 1.155768 |    0.238164 |    0.0 | 1.155768 |
    | 13.01. |    0.0 |       1.882449 | 1.155647 |    0.138316 |    0.0 | 1.155647 |
    | 14.01. |    0.0 |       0.940746 | 0.908959 |    0.059782 |    0.0 | 0.908959 |
    | 15.01. |    0.0 |       0.400649 | 0.400648 |    0.025166 |    0.0 | 0.400648 |
    | 16.01. |    0.0 |       0.167488 | 0.167488 |    0.010695 |    0.0 | 0.167488 |
    | 17.01. |    0.0 |       0.071178 | 0.071178 |    0.004545 |    0.0 | 0.071178 |
    | 18.01. |    0.0 |        0.03147 |  0.03147 |    0.001826 |    0.0 |  0.03147 |
    | 19.01. |    0.0 |       0.010371 | 0.010371 |     0.00093 |    0.0 | 0.010371 |
    | 20.01. |    0.0 |       0.005282 | 0.005282 |    0.000474 |    0.0 | 0.005282 |
"""
# import...
# ...from HydPy
from hydpy.auxs.anntools import ann  # pylint: disable=unused-import
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

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
    INLET_METHODS = (dam_model.Pic_Inflow_V1,)
    RECEIVER_METHODS = ()
    ADD_METHODS = (dam_model.Fix_Min1_V1,)
    PART_ODE_METHODS = (
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_SurfaceArea_V1,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_AllowedDischarge_V1,
        dam_model.Calc_Outflow_V2,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V1,)
    OUTLET_METHODS = (dam_model.Pass_Outflow_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
