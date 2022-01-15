# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Version 4 of HydPy-Dam.

Application model |dam_v004| extends |dam_v003|.  Both models discharge water into the
channel downstream and to "remote locations".  The difference is that |dam_v003|
releases water only to a single remote location (for example, to a drinking water
treatment plant) while |dam_v004| also discharges to a second remote location (for
example, to relieve water during high flow conditions).

The following explanations focus on this difference.  For further information on using
|dam_v004|, please read the documentation on |dam_v001| and |dam_v003|.  Besides that,
consider reading the documentation on |dam_v005|, which is a possible counterpart to
|dam_v004|, being able to send information on required supply and allowed relief and to
consume the related discharges.

Integration tests
=================

.. how_to_understand_integration_tests::

The following examples stem from the documentation of application model |dam_v003|.
Some are recalculations to confirm the proper implementation of the features common
to both models.  Others are modifications that illustrate the additional features
of |dam_v003|.

The time-related setup is identical to the one of |dam_v003|:

>>> from hydpy import pub, Node, Element
>>> pub.timegrids = "01.01.2000", "21.01.2000", "1d"

In addition to the general configuration of application model |dam_v003|, we require
connections to two additional |Node| objects.  Node `allowed_relief` provides
information on the maximum allowed relief discharge, and node `actual_relief` passes
the actual relief discharge to a remote location. Both nodes use the string literal "R"
to connect to the receiver sequence |dam_receivers.R| and the outlet sequence
|dam_outlets.R|, respectively:

>>> inflow = Node("inflow", variable="Q")
>>> outflow = Node("outflow", variable="Q")
>>> required_supply = Node("required_supply", variable="S")
>>> actual_supply = Node("actual_supply", variable="S")
>>> allowed_relief = Node("allowed_relief", variable="R")
>>> actual_relief = Node("actual_relief", variable="R")
>>> dam = Element("dam",
...               inlets=inflow,
...               outlets=(outflow, actual_supply, actual_relief),
...               receivers=(required_supply, allowed_relief))
>>> from hydpy.models.dam_v004 import *
>>> parameterstep("1d")
>>> dam.model = model

We prepare the |IntegrationTest| object as for |dam_v003|:

>>> from hydpy import IntegrationTest
>>> test = IntegrationTest(dam)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = states.watervolume

|dam_v004| requires additional initial conditions for the sequence
|LoggedAllowedRemoteRelief|:

>>> test.inits=((states.watervolume, 0.0),
...             (logs.loggedadjustedevaporation, 0.0),
...             (logs.loggedrequiredremoterelease, 0.005),
...             (logs.loggedallowedremoterelief, 0.0))

We define the same inflow, |dam_inputs.Precipitation|, and |dam_inputs.Evaporation|
time series as for |dam_v003|:

>>> inflow.sequences.sim.series = 1.0
>>> inputs.precipitation.series = 0.0
>>> inputs.evaporation.series = 0.0

|dam_v003| and |dam_v004| share the following parameters and we apply the same values
as for |dam_v003|:

>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 0.25]))
>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0], ys=[0.0]))
>>> catchmentarea(86.4)
>>> neardischargeminimumthreshold(0.2)
>>> neardischargeminimumtolerance(0.2)
>>> waterlevelminimumthreshold(0.0)
>>> waterlevelminimumtolerance(0.0)
>>> waterlevelminimumremotethreshold(0.0)
>>> waterlevelminimumremotetolerance(0.0)
>>> restricttargetedrelease(True)
>>> surfacearea(1.44)
>>> correctionprecipitation(1.2)
>>> correctionevaporation(1.2)
>>> weightevaporation(0.8)
>>> thresholdevaporation(0.0)
>>> toleranceevaporation(0.001)

The following parameters are unique to |dam_v004|.  We first set "neutral" values
which disable any relief discharges:

>>> remoterelieftolerance(0.0)
>>> highestremotedischarge(inf)
>>> highestremotetolerance(0.1)
>>> waterlevel2possibleremoterelief(PPoly.from_data(xs=[0.0], ys=[0.0]))
>>> figure = waterlevel2possibleremoterelief.plot(-0.1, 1.0)
>>> from hydpy.core.testtools import save_autofig
>>> save_autofig("dam_v004_waterlevel2possibleremoterelief_1.png", figure=figure)

.. image:: dam_v004_waterlevel2possibleremoterelief_1.png
   :width: 400

.. _dam_v004_smooth_near_minimum:

smooth near minimum
___________________

The following examples correspond to the :ref:`dam_v001_smooth_near_minimum` example of
application model |dam_v001| as well as the :ref:`dam_v003_smooth_near_minimum` example
of application model |dam_v003|.  We again use the same remote demand:

>>> required_supply.sequences.sim.series = [
...     0.008588, 0.010053, 0.013858, 0.027322, 0.064075, 0.235523, 0.470414,
...     0.735001, 0.891263, 0.696325, 0.349797, 0.105231, 0.111928, 0.240436,
...     0.229369, 0.058622, 0.016958, 0.008447, 0.004155, 0.0]

.. _dam_v004_smooth_near_minimum_recalculation:

recalculation
-------------

To first perform a strict recalculation, we set the allowed discharge relief to zero:

>>> allowed_relief.sequences.sim.series = 0.0

This recalculation confirms that model |dam_v004| functions exactly like model |dam_v003|
to meet the water demands at a cross-section downstream and a single remote location
(for example, see column "waterlevel"):

.. integration-test::

    >>> test("dam_v004_smooth_near_minimum_recalculation",
    ...      axis1=(fluxes.inflow, fluxes.outflow, fluxes.actualremoterelease),
    ...      axis2=states.watervolume)
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017356 |                   0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 |           0.0 |      0.004792 |            0.0 |    1.0 | 0.191667 |        0.008588 |
    | 02.01. |           0.0 |         0.0 |   0.034451 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008588 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.008588 |            0.0 |      0.2 |    0.137804 |           0.0 |      0.008588 |            0.0 |    1.0 |      0.2 |        0.010053 |
    | 03.01. |           0.0 |         0.0 |   0.051514 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.010053 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.010053 |            0.0 |      0.2 |    0.206055 |           0.0 |      0.010053 |            0.0 |    1.0 |      0.2 |        0.013858 |
    | 04.01. |           0.0 |         0.0 |   0.068495 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.013858 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.013858 |            0.0 |      0.2 |    0.273978 |           0.0 |      0.013858 |            0.0 |    1.0 |      0.2 |        0.027322 |
    | 05.01. |           0.0 |         0.0 |   0.085184 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.027322 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.027322 |            0.0 |      0.2 |    0.340737 |           0.0 |      0.027322 |            0.0 |    1.0 |      0.2 |        0.064075 |
    | 06.01. |           0.0 |         0.0 |    0.10108 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.064075 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.064075 |            0.0 |      0.2 |    0.404321 |           0.0 |      0.064075 |            0.0 |    1.0 |      0.2 |        0.235523 |
    | 07.01. |           0.0 |         0.0 |   0.113273 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.235523 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.235523 |            0.0 |      0.2 |    0.453092 |           0.0 |      0.235523 |            0.0 |    1.0 |      0.2 |        0.470414 |
    | 08.01. |           0.0 |         0.0 |   0.120392 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.470414 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.470414 |            0.0 |      0.2 |    0.481568 |           0.0 |      0.470414 |            0.0 |    1.0 |      0.2 |        0.735001 |
    | 09.01. |           0.0 |         0.0 |   0.121796 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.735001 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.735001 |            0.0 |      0.2 |    0.487184 |           0.0 |      0.735001 |            0.0 |    1.0 |      0.2 |        0.891263 |
    | 10.01. |           0.0 |         0.0 |   0.119825 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.891263 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.891263 |            0.0 |      0.2 |    0.479299 |           0.0 |      0.891263 |            0.0 |    1.0 |      0.2 |        0.696325 |
    | 11.01. |           0.0 |         0.0 |   0.122064 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.696325 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.696325 |            0.0 |      0.2 |    0.488257 |           0.0 |      0.696325 |            0.0 |    1.0 |      0.2 |        0.349797 |
    | 12.01. |           0.0 |         0.0 |   0.131789 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.349797 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.349797 |            0.0 |      0.2 |    0.527154 |           0.0 |      0.349797 |            0.0 |    1.0 |      0.2 |        0.105231 |
    | 13.01. |           0.0 |         0.0 |   0.146796 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.105231 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.105231 |            0.0 |      0.2 |    0.587182 |           0.0 |      0.105231 |            0.0 |    1.0 |      0.2 |        0.111928 |
    | 14.01. |           0.0 |         0.0 |   0.161658 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.111928 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.111928 |            0.0 |      0.2 |    0.646632 |           0.0 |      0.111928 |            0.0 |    1.0 |      0.2 |        0.240436 |
    | 15.01. |           0.0 |         0.0 |   0.173745 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.240436 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.240436 |            0.0 |      0.2 |    0.694978 |           0.0 |      0.240436 |            0.0 |    1.0 |      0.2 |        0.229369 |
    | 16.01. |           0.0 |         0.0 |    0.18607 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.229369 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.229369 |            0.0 |      0.2 |    0.744281 |           0.0 |      0.229369 |            0.0 |    1.0 |      0.2 |        0.058622 |
    | 17.01. |           0.0 |         0.0 |   0.202084 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.058622 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.058622 |            0.0 |      0.2 |    0.808336 |           0.0 |      0.058622 |            0.0 |    1.0 |      0.2 |        0.016958 |
    | 18.01. |           0.0 |         0.0 |   0.218998 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.016958 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.016958 |            0.0 |      0.2 |     0.87599 |           0.0 |      0.016958 |            0.0 |    1.0 |      0.2 |        0.008447 |
    | 19.01. |           0.0 |         0.0 |   0.236095 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008447 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.008447 |            0.0 |      0.2 |    0.944381 |           0.0 |      0.008447 |            0.0 |    1.0 |      0.2 |        0.004155 |
    | 20.01. |           0.0 |         0.0 |   0.253285 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.004155 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.004155 |            0.0 |      0.2 |    1.013142 |           0.0 |      0.004155 |            0.0 |    1.0 |      0.2 |             0.0 |

.. _dam_v004_smooth_near_minimum_modification_1:

modification 1
--------------

In this first modification of the :ref:`dam_v003_smooth_near_minimum` example, we take
the old required supply as the new allowed relief discharge and set the new required
supply to zero:

>>> allowed_relief.sequences.sim.series = required_supply.sequences.sim.series
>>> test.inits.loggedallowedremoterelief = 0.005
>>> required_supply.sequences.sim.series = 0.0
>>> test.inits.loggedrequiredremoterelease = 0.0

Also, we set the possible relief discharge to a huge constant value of 100 m³/s:

>>> waterlevel2possibleremoterelief(PPoly.from_data(xs=[0.0], ys=[100.0]))
>>> figure = waterlevel2possibleremoterelief.plot(-0.1, 1.0)
>>> from hydpy.core.testtools import save_autofig
>>> save_autofig("dam_v004_waterlevel2possibleremoterelief_2.png", figure=figure)

.. image:: dam_v001_waterlevel2flooddischarge_2.png
   :width: 400

Due to this setting, the new actual relief discharge is nearly identical to the old
actual supply discharge.  There is only a minor deviation in the first simulation step
due to the numerical inaccuracy explained in the documentation on |dam_v001|:

.. integration-test::

    >>> test("dam_v004_smooth_near_minimum_modification_1",
    ...      axis1=(fluxes.inflow, fluxes.outflow, fluxes.actualremoterelief),
    ...      axis2=states.watervolume)
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017352 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |               0.005 |                100.0 |              0.005 |             0.2 |             0.2 |      0.191667 |                 0.0 |            0.0 | 0.191667 |    0.069408 |         0.005 |           0.0 |       0.008588 |    1.0 | 0.191667 |             0.0 |
    | 02.01. |           0.0 |         0.0 |   0.034446 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008588 |                100.0 |           0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137786 |      0.008588 |           0.0 |       0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.051509 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.010053 |                100.0 |           0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.206037 |      0.010053 |           0.0 |       0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |           0.0 |         0.0 |    0.06849 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.013858 |                100.0 |           0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.27396 |      0.013858 |           0.0 |       0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |           0.0 |         0.0 |    0.08518 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.027322 |                100.0 |           0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340719 |      0.027322 |           0.0 |       0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.101076 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.064075 |                100.0 |           0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.404303 |      0.064075 |           0.0 |       0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.113269 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.235523 |                100.0 |           0.235523 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.453074 |      0.235523 |           0.0 |       0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.120388 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.470414 |                100.0 |           0.470414 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.48155 |      0.470414 |           0.0 |       0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.121792 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.735001 |                100.0 |           0.735001 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.487166 |      0.735001 |           0.0 |       0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |           0.0 |         0.0 |    0.11982 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.891263 |                100.0 |           0.891263 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.479281 |      0.891263 |           0.0 |       0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |           0.0 |         0.0 |    0.12206 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.696325 |                100.0 |           0.696325 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.488239 |      0.696325 |           0.0 |       0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.131784 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.349797 |                100.0 |           0.349797 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.527136 |      0.349797 |           0.0 |       0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |           0.0 |         0.0 |   0.146791 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.105231 |                100.0 |           0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.587164 |      0.105231 |           0.0 |       0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.161653 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.111928 |                100.0 |           0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.646614 |      0.111928 |           0.0 |       0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |           0.0 |         0.0 |    0.17374 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.240436 |                100.0 |           0.240436 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.69496 |      0.240436 |           0.0 |       0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.186066 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.229369 |                100.0 |           0.229369 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.744263 |      0.229369 |           0.0 |       0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.202079 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.058622 |                100.0 |           0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.808318 |      0.058622 |           0.0 |       0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.218993 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.016958 |                100.0 |           0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.875972 |      0.016958 |           0.0 |       0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.236091 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008447 |                100.0 |           0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.944363 |      0.008447 |           0.0 |       0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.253281 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.004155 |                100.0 |           0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.013124 |      0.004155 |           0.0 |            0.0 |    1.0 |      0.2 |             0.0 |

.. _dam_v004_smooth_near_minimum_modification_2:

modification 2
--------------

Now, we modify |WaterLevel2PossibleRemoteRelief| to prevent any relief discharge when
the dam is empty and to set its maximum to 0.5 m³/s:

>>> waterlevel2possibleremoterelief(ANN(weights_input=1e30, weights_output=0.5,
...                                     intercepts_hidden=-1e27, intercepts_output=0.0))
>>> waterlevel2possibleremoterelief(PPoly(Poly(x0=-1.0, cs=(0.0,)), Poly(x0=0.0, cs=(0.5,))))
>>> figure = waterlevel2possibleremoterelief.plot(-0.1, 1.0)
>>> from hydpy.core.testtools import save_autofig
>>> save_autofig("dam_v004_waterlevel2possibleremoterelief_3.png", figure=figure)

.. image:: dam_v001_waterlevel2flooddischarge_3.png
   :width: 400

For low water levels, the current customisation of the possible relief discharge
resembles the customisation of the actual supply defined in the
:ref:`dam_v004_smooth_near_minimum_recalculation` example.  Hence, the results for
|ActualRemoteRelease| and |ActualRemoteRelief| of the respective experiments agree
well (again, except for the minor deviation for the first simulation step due to
limited numerical accuracy).  For the high water levels (between January 9 and January
11), the imposed restriction of 0.5 m³/s  results in a reduced relief discharge:

.. integration-test::

    >>> test("dam_v004_smooth_near_minimum_modification_2",
    ...      axis1=(fluxes.inflow, fluxes.outflow, fluxes.actualremoterelief),
    ...      axis2=states.watervolume)
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017352 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |               0.005 |                  0.5 |              0.005 |             0.2 |             0.2 |      0.191667 |                 0.0 |            0.0 | 0.191667 |    0.069408 |         0.005 |           0.0 |       0.008588 |    1.0 | 0.191667 |             0.0 |
    | 02.01. |           0.0 |         0.0 |   0.034446 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008588 |                  0.5 |           0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137786 |      0.008588 |           0.0 |       0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.051509 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.010053 |                  0.5 |           0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.206037 |      0.010053 |           0.0 |       0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |           0.0 |         0.0 |    0.06849 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.013858 |                  0.5 |           0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.27396 |      0.013858 |           0.0 |       0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |           0.0 |         0.0 |    0.08518 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.027322 |                  0.5 |           0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340719 |      0.027322 |           0.0 |       0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.101076 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.064075 |                  0.5 |           0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.404303 |      0.064075 |           0.0 |       0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.113269 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.235523 |                  0.5 |           0.235523 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.453074 |      0.235523 |           0.0 |       0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.120388 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.470414 |                  0.5 |           0.470414 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.48155 |      0.470414 |           0.0 |       0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.126868 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.735001 |                  0.5 |                0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.50747 |           0.5 |           0.0 |       0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |           0.0 |         0.0 |   0.133348 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.891263 |                  0.5 |                0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.53339 |           0.5 |           0.0 |       0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.139828 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.696325 |                  0.5 |                0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.55931 |           0.5 |           0.0 |       0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.149552 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.349797 |                  0.5 |           0.349797 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.598208 |      0.349797 |           0.0 |       0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |           0.0 |         0.0 |   0.164559 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.105231 |                  0.5 |           0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.658236 |      0.105231 |           0.0 |       0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.179421 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.111928 |                  0.5 |           0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.717685 |      0.111928 |           0.0 |       0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |           0.0 |         0.0 |   0.191508 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.240436 |                  0.5 |           0.240436 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.766032 |      0.240436 |           0.0 |       0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.203834 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.229369 |                  0.5 |           0.229369 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.815334 |      0.229369 |           0.0 |       0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.219847 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.058622 |                  0.5 |           0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.879389 |      0.058622 |           0.0 |       0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.236761 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.016958 |                  0.5 |           0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.947044 |      0.016958 |           0.0 |       0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.253859 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008447 |                  0.5 |           0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.015434 |      0.008447 |           0.0 |       0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.271049 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.004155 |                  0.5 |           0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.084195 |      0.004155 |           0.0 |            0.0 |    1.0 |      0.2 |             0.0 |

.. _dam_v004_smooth_near_minimum_modification_3:

modification 3
--------------

The restricted possible relief discharge in the example above results in a discontinuous
evolution of the actual relief discharge.  To achieve smoother transitions, one can set
|RemoteReliefTolerance| to a value larger than zero:

.. integration-test::

    >>> remoterelieftolerance(0.2)
    >>> test("dam_v004_smooth_near_minimum_modification_3",
    ...      axis1=(fluxes.inflow, fluxes.outflow, fluxes.actualremoterelief),
    ...      axis2=states.watervolume)
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017352 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |               0.005 |                  0.5 |              0.005 |             0.2 |             0.2 |      0.191667 |                 0.0 |            0.0 | 0.191667 |    0.069408 |         0.005 |           0.0 |       0.008588 |    1.0 | 0.191667 |             0.0 |
    | 02.01. |           0.0 |         0.0 |   0.034446 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008588 |                  0.5 |           0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137786 |      0.008588 |           0.0 |       0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.051509 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.010053 |                  0.5 |           0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.206037 |      0.010053 |           0.0 |       0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |           0.0 |         0.0 |    0.06849 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.013858 |                  0.5 |           0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.27396 |      0.013858 |           0.0 |       0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |           0.0 |         0.0 |    0.08518 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.027322 |                  0.5 |           0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340719 |      0.027322 |           0.0 |       0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.101076 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.064075 |                  0.5 |           0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.404303 |      0.064075 |           0.0 |       0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.113272 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.235523 |                  0.5 |           0.235352 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.453089 |      0.235352 |           0.0 |       0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.121505 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.470414 |                  0.5 |           0.418836 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.486022 |      0.418836 |           0.0 |       0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.128571 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.735001 |                  0.5 |           0.472874 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.514285 |      0.472874 |           0.0 |       0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |           0.0 |         0.0 |   0.135468 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.891263 |                  0.5 |           0.480688 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.541874 |      0.480688 |           0.0 |       0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.142606 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.696325 |                  0.5 |           0.469547 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.570425 |      0.469547 |           0.0 |       0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.152498 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.349797 |                  0.5 |           0.342067 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.60999 |      0.342067 |           0.0 |       0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |           0.0 |         0.0 |   0.167505 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.105231 |                  0.5 |           0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.670018 |      0.105231 |           0.0 |       0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.182367 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.111928 |                  0.5 |           0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.729468 |      0.111928 |           0.0 |       0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |           0.0 |         0.0 |   0.194458 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.240436 |                  0.5 |           0.240219 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.777833 |      0.240219 |           0.0 |       0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.206787 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.229369 |                  0.5 |           0.229243 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.827146 |      0.229243 |           0.0 |       0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |           0.0 |         0.0 |     0.2228 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.058622 |                  0.5 |           0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.891201 |      0.058622 |           0.0 |       0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.239714 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.016958 |                  0.5 |           0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.958856 |      0.016958 |           0.0 |       0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.256812 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008447 |                  0.5 |           0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.027246 |      0.008447 |           0.0 |       0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.274002 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.004155 |                  0.5 |           0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.096007 |      0.004155 |           0.0 |            0.0 |    1.0 |      0.2 |             0.0 |

.. _dam_v004_restriction_enabled:

restriction enabled
___________________

The following exact recalculations demonstrate the identical functioning of those
components of |dam_v004| and |dam_v003| not utilised in the examples above.  Therefore,
we disable the remote relief discharge again:

>>> test.inits.loggedrequiredremoterelease = 0.005
>>> test.inits.loggedallowedremoterelief = 0.0
>>> waterlevelminimumremotetolerance(0.0)
>>> waterlevel2possibleremoterelief(PPoly.from_data(xs=[0.0], ys=[0.0]))
>>> remoterelieftolerance(0.0)
>>> allowed_relief.sequences.sim.series = 0.0

Here, we confirm equality when releasing water to the channel downstream during low
flow conditions.  We need to update the time series of the inflow and the required
remote release:

>>> inflow.sequences.sim.series[10:] = 0.1
>>> required_supply.sequences.sim.series = [
...     0.008746, 0.010632, 0.015099, 0.03006, 0.068641, 0.242578, 0.474285, 0.784512,
...     0.95036, 0.35, 0.034564, 0.299482, 0.585979, 0.557422, 0.229369, 0.142578,
...     0.068641, 0.029844, 0.012348, 0.0]
>>> neardischargeminimumtolerance(0.0)

The following results agree with the test results of the
:ref:`dam_v003_restriction_enabled` example of application model |dam_v003|:

.. integration-test::

    >>> test("dam_v004_restriction_enabled")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.017357 |                   0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 |           0.0 |      0.004792 |            0.0 |    1.0 | 0.191667 |        0.008746 |
    | 02.01. |           0.0 |         0.0 |   0.034448 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008746 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.008746 |            0.0 |      0.2 |     0.13779 |           0.0 |      0.008746 |            0.0 |    1.0 |      0.2 |        0.010632 |
    | 03.01. |           0.0 |         0.0 |   0.051498 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.010632 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.010632 |            0.0 |      0.2 |    0.205992 |           0.0 |      0.010632 |            0.0 |    1.0 |      0.2 |        0.015099 |
    | 04.01. |           0.0 |         0.0 |   0.068452 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.015099 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.015099 |            0.0 |      0.2 |    0.273807 |           0.0 |      0.015099 |            0.0 |    1.0 |      0.2 |         0.03006 |
    | 05.01. |           0.0 |         0.0 |   0.085083 |                   0.0 |                 0.0 |               0.0 |    1.0 |               0.03006 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |             0.03006 |            0.0 |      0.2 |     0.34033 |           0.0 |       0.03006 |            0.0 |    1.0 |      0.2 |        0.068641 |
    | 06.01. |           0.0 |         0.0 |    0.10088 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.068641 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.068641 |            0.0 |      0.2 |    0.403519 |           0.0 |      0.068641 |            0.0 |    1.0 |      0.2 |        0.242578 |
    | 07.01. |           0.0 |         0.0 |    0.11292 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.242578 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.242578 |            0.0 |      0.2 |    0.451681 |           0.0 |      0.242578 |            0.0 |    1.0 |      0.2 |        0.474285 |
    | 08.01. |           0.0 |         0.0 |   0.119956 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.474285 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.474285 |            0.0 |      0.2 |    0.479822 |           0.0 |      0.474285 |            0.0 |    1.0 |      0.2 |        0.784512 |
    | 09.01. |           0.0 |         0.0 |    0.12029 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.784512 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.784512 |            0.0 |      0.2 |    0.481161 |           0.0 |      0.784512 |            0.0 |    1.0 |      0.2 |         0.95036 |
    | 10.01. |           0.0 |         0.0 |   0.117042 |                   0.0 |                 0.0 |               0.0 |    1.0 |               0.95036 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |             0.95036 |            0.0 |      0.2 |     0.46817 |           0.0 |       0.95036 |            0.0 |    1.0 |      0.2 |            0.35 |
    | 11.01. |           0.0 |         0.0 |   0.109482 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  0.35 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |                0.35 |            0.0 |      0.1 |     0.43793 |           0.0 |          0.35 |            0.0 |    0.1 |      0.1 |        0.034564 |
    | 12.01. |           0.0 |         0.0 |   0.108736 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.034564 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.034564 |            0.0 |      0.1 |    0.434943 |           0.0 |      0.034564 |            0.0 |    0.1 |      0.1 |        0.299482 |
    | 13.01. |           0.0 |         0.0 |   0.102267 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.299482 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.299482 |            0.0 |      0.1 |    0.409068 |           0.0 |      0.299482 |            0.0 |    0.1 |      0.1 |        0.585979 |
    | 14.01. |           0.0 |         0.0 |    0.08961 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.585979 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.585979 |            0.0 |      0.1 |    0.358439 |           0.0 |      0.585979 |            0.0 |    0.1 |      0.1 |        0.557422 |
    | 15.01. |           0.0 |         0.0 |    0.07757 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.557422 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.557422 |            0.0 |      0.1 |    0.310278 |           0.0 |      0.557422 |            0.0 |    0.1 |      0.1 |        0.229369 |
    | 16.01. |           0.0 |         0.0 |   0.072615 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.229369 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.229369 |            0.0 |      0.1 |    0.290461 |           0.0 |      0.229369 |            0.0 |    0.1 |      0.1 |        0.142578 |
    | 17.01. |           0.0 |         0.0 |   0.069535 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.142578 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.142578 |            0.0 |      0.1 |    0.278142 |           0.0 |      0.142578 |            0.0 |    0.1 |      0.1 |        0.068641 |
    | 18.01. |           0.0 |         0.0 |   0.068053 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.068641 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.068641 |            0.0 |      0.1 |    0.272211 |           0.0 |      0.068641 |            0.0 |    0.1 |      0.1 |        0.029844 |
    | 19.01. |           0.0 |         0.0 |   0.067408 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.029844 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.029844 |            0.0 |      0.1 |    0.269633 |           0.0 |      0.029844 |            0.0 |    0.1 |      0.1 |        0.012348 |
    | 20.01. |           0.0 |         0.0 |   0.067141 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.012348 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.012348 |            0.0 |      0.1 |    0.268566 |           0.0 |      0.012348 |            0.0 |    0.1 |      0.1 |             0.0 |

.. _dam_v004_smooth_stage_minimum:

smooth stage minimum
____________________

This example repeats the :ref:`dam_v003_smooth_stage_minimum` example of application
model |dam_v003|.  We update all parameter and time series accordingly:

>>> waterlevelminimumtolerance(0.01)
>>> waterlevelminimumthreshold(0.005)
>>> waterlevelminimumremotetolerance(0.01)
>>> waterlevelminimumremotethreshold(0.01)
>>> inflow.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)
>>> required_supply.sequences.sim.series = [
...     0.01232, 0.029323, 0.064084, 0.120198, 0.247367, 0.45567, 0.608464,
...     0.537314, 0.629775, 0.744091, 0.82219, 0.841916, 0.701812, 0.533258,
...     0.351863, 0.185207, 0.107697, 0.055458, 0.025948, 0.0]

|dam_v004| responds equally to limited storage contents as |dam_v003|:

.. integration-test::

    >>> test("dam_v004_smooth_stage_minimum")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   inflow |  outflow | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   0.003486 |                   0.0 |                 0.0 |               0.0 |      0.2 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.038491 |             0.00012 |            0.0 | 0.038491 |    0.013944 |           0.0 |       0.00012 |            0.0 |      0.2 | 0.038491 |         0.01232 |
    | 02.01. |           0.0 |         0.0 |   0.005678 |                   0.0 |                 0.0 |               0.0 | 0.189474 |               0.01232 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.189474 |      0.086988 |            0.000993 |            0.0 | 0.086988 |    0.022713 |           0.0 |      0.000993 |            0.0 | 0.189474 | 0.086988 |        0.029323 |
    | 03.01. |           0.0 |         0.0 |   0.006935 |                   0.0 |                 0.0 |               0.0 | 0.178947 |              0.029323 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.178947 |      0.116103 |            0.004642 |            0.0 | 0.116103 |    0.027742 |           0.0 |      0.004642 |            0.0 | 0.178947 | 0.116103 |        0.064084 |
    | 04.01. |           0.0 |         0.0 |   0.007554 |                   0.0 |                 0.0 |               0.0 | 0.168421 |              0.064084 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.168421 |      0.125159 |            0.014625 |            0.0 | 0.125159 |    0.030216 |           0.0 |      0.014625 |            0.0 | 0.168421 | 0.125159 |        0.120198 |
    | 05.01. |           0.0 |         0.0 |    0.00768 |                   0.0 |                 0.0 |               0.0 | 0.157895 |              0.120198 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.157895 |      0.121681 |            0.030361 |            0.0 | 0.121681 |    0.030722 |           0.0 |      0.030361 |            0.0 | 0.157895 | 0.121681 |        0.247367 |
    | 06.01. |           0.0 |         0.0 |   0.007261 |                   0.0 |                 0.0 |               0.0 | 0.147368 |              0.247367 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.147368 |      0.109923 |            0.056857 |            0.0 | 0.109923 |    0.029044 |           0.0 |      0.056857 |            0.0 | 0.147368 | 0.109923 |         0.45567 |
    | 07.01. |           0.0 |         0.0 |   0.006338 |                   0.0 |                 0.0 |               0.0 | 0.136842 |               0.45567 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.136842 |      0.094858 |            0.084715 |            0.0 | 0.094858 |    0.025352 |           0.0 |      0.084715 |            0.0 | 0.136842 | 0.094858 |        0.608464 |
    | 08.01. |           0.0 |         0.0 |   0.005622 |                   0.0 |                 0.0 |               0.0 | 0.126316 |              0.608464 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.126316 |      0.076914 |            0.082553 |            0.0 | 0.076914 |    0.022488 |           0.0 |      0.082553 |            0.0 | 0.126316 | 0.076914 |        0.537314 |
    | 09.01. |           0.0 |         0.0 |   0.005446 |                   0.0 |                 0.0 |               0.0 | 0.115789 |              0.537314 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.115789 |      0.064167 |            0.059779 |            0.0 | 0.064167 |    0.021783 |           0.0 |      0.059779 |            0.0 | 0.115789 | 0.064167 |        0.629775 |
    | 10.01. |           0.0 |         0.0 |   0.005167 |                   0.0 |                 0.0 |               0.0 | 0.105263 |              0.629775 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.105263 |      0.055154 |            0.063011 |            0.0 | 0.055154 |    0.020669 |           0.0 |      0.063011 |            0.0 | 0.105263 | 0.055154 |        0.744091 |
    | 11.01. |           0.0 |         0.0 |   0.004819 |                   0.0 |                 0.0 |               0.0 | 0.094737 |              0.744091 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.094737 |      0.045986 |            0.064865 |            0.0 | 0.045986 |    0.019277 |           0.0 |      0.064865 |            0.0 | 0.094737 | 0.045986 |         0.82219 |
    | 12.01. |           0.0 |         0.0 |   0.004479 |                   0.0 |                 0.0 |               0.0 | 0.084211 |               0.82219 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.084211 |      0.037699 |             0.06228 |            0.0 | 0.037699 |    0.017914 |           0.0 |       0.06228 |            0.0 | 0.084211 | 0.037699 |        0.841916 |
    | 13.01. |           0.0 |         0.0 |   0.004191 |                   0.0 |                 0.0 |               0.0 | 0.073684 |              0.841916 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.073684 |      0.030632 |            0.056377 |            0.0 | 0.030632 |    0.016763 |           0.0 |      0.056377 |            0.0 | 0.073684 | 0.030632 |        0.701812 |
    | 14.01. |           0.0 |         0.0 |   0.004065 |                   0.0 |                 0.0 |               0.0 | 0.063158 |              0.701812 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.063158 |      0.025166 |            0.043828 |            0.0 | 0.025166 |    0.016259 |           0.0 |      0.043828 |            0.0 | 0.063158 | 0.025166 |        0.533258 |
    | 15.01. |           0.0 |         0.0 |    0.00405 |                   0.0 |                 0.0 |               0.0 | 0.052632 |              0.533258 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.052632 |      0.020693 |            0.032602 |            0.0 | 0.020693 |    0.016201 |           0.0 |      0.032602 |            0.0 | 0.052632 | 0.020693 |        0.351863 |
    | 16.01. |           0.0 |         0.0 |   0.004126 |                   0.0 |                 0.0 |               0.0 | 0.042105 |              0.351863 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.042105 |      0.016736 |            0.021882 |            0.0 | 0.016736 |    0.016502 |           0.0 |      0.021882 |            0.0 | 0.042105 | 0.016736 |        0.185207 |
    | 17.01. |           0.0 |         0.0 |   0.004268 |                   0.0 |                 0.0 |               0.0 | 0.031579 |              0.185207 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.031579 |      0.012934 |            0.012076 |            0.0 | 0.012934 |     0.01707 |           0.0 |      0.012076 |            0.0 | 0.031579 | 0.012934 |        0.107697 |
    | 18.01. |           0.0 |         0.0 |    0.00437 |                   0.0 |                 0.0 |               0.0 | 0.021053 |              0.107697 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.021053 |      0.008901 |            0.007386 |            0.0 | 0.008901 |    0.017482 |           0.0 |      0.007386 |            0.0 | 0.021053 | 0.008901 |        0.055458 |
    | 19.01. |           0.0 |         0.0 |   0.004415 |                   0.0 |                 0.0 |               0.0 | 0.010526 |              0.055458 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.010526 |      0.004535 |             0.00392 |            0.0 | 0.004535 |    0.017661 |           0.0 |       0.00392 |            0.0 | 0.010526 | 0.004535 |        0.025948 |
    | 20.01. |           0.0 |         0.0 |   0.004376 |                   0.0 |                 0.0 |               0.0 |      0.0 |              0.025948 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.0 |           0.0 |            0.001835 |            0.0 |      0.0 |    0.017502 |           0.0 |      0.001835 |            0.0 |      0.0 |      0.0 |             0.0 |

.. _dam_v004_evaporation:

evaporation
___________

This example repeats the :ref:`dam_v003_evaporation` example of application model
|dam_v003|.  We update the time series of potential evaporation and the required remote
release accordingly:

>>> inputs.evaporation.series = 10 * [1.0] + 10 * [5.0]
>>> required_supply.sequences.sim.series = [
...     0.012321, 0.029352, 0.064305, 0.120897, 0.248435, 0.453671, 0.585089,
...     0.550583, 0.694398, 0.784979, 0.81852, 0.840207, 0.72592, 0.575373,
...     0.386003, 0.198088, 0.113577, 0.05798, 0.026921, 0.0]

.. integration-test::

    >>> test("dam_v004_evaporation")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation |   inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief |   inflow |  outflow | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         1.0 |   0.003204 |                   0.0 |               0.016 |          0.014663 |      0.2 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.036881 |            0.000114 |            0.0 | 0.036881 |    0.012817 |           0.0 |      0.000114 |            0.0 |      0.2 | 0.036881 |        0.012321 |
    | 02.01. |           0.0 |         1.0 |   0.005171 |                   0.0 |              0.0192 |            0.0192 | 0.189474 |              0.012321 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.189474 |      0.078396 |            0.000832 |            0.0 | 0.078396 |    0.020683 |           0.0 |      0.000832 |            0.0 | 0.189474 | 0.078396 |        0.029352 |
    | 03.01. |           0.0 |         1.0 |   0.006267 |                   0.0 |             0.01984 |           0.01984 | 0.178947 |              0.029352 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.178947 |      0.104667 |             0.00367 |            0.0 | 0.104667 |     0.02507 |           0.0 |       0.00367 |            0.0 | 0.178947 | 0.104667 |        0.064305 |
    | 04.01. |           0.0 |         1.0 |   0.006777 |                   0.0 |            0.019968 |          0.019968 | 0.168421 |              0.064305 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.168421 |      0.113657 |            0.011204 |            0.0 | 0.113657 |    0.027108 |           0.0 |      0.011204 |            0.0 | 0.168421 | 0.113657 |        0.120897 |
    | 05.01. |           0.0 |         1.0 |   0.006873 |                   0.0 |            0.019994 |          0.019994 | 0.157895 |              0.120897 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.157895 |      0.110489 |            0.022953 |            0.0 | 0.110489 |    0.027493 |           0.0 |      0.022953 |            0.0 | 0.157895 | 0.110489 |        0.248435 |
    | 06.01. |           0.0 |         1.0 |   0.006531 |                   0.0 |            0.019999 |          0.019999 | 0.147368 |              0.248435 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.147368 |      0.099756 |            0.043467 |            0.0 | 0.099756 |    0.026124 |           0.0 |      0.043467 |            0.0 | 0.147368 | 0.099756 |        0.453671 |
    | 07.01. |           0.0 |         1.0 |   0.005779 |                   0.0 |                0.02 |              0.02 | 0.136842 |              0.453671 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.136842 |      0.085828 |            0.065832 |            0.0 | 0.085828 |    0.023115 |           0.0 |      0.065832 |            0.0 | 0.136842 | 0.085828 |        0.585089 |
    | 08.01. |           0.0 |         1.0 |   0.005171 |                   0.0 |                0.02 |              0.02 | 0.126316 |              0.585089 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.126316 |      0.069773 |            0.064688 |            0.0 | 0.069773 |    0.020684 |           0.0 |      0.064688 |            0.0 | 0.126316 | 0.069773 |        0.550583 |
    | 09.01. |           0.0 |         1.0 |    0.00492 |                   0.0 |                0.02 |              0.02 | 0.115789 |              0.550583 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.115789 |      0.057531 |            0.049863 |            0.0 | 0.057531 |    0.019681 |           0.0 |      0.049863 |            0.0 | 0.115789 | 0.057531 |        0.694398 |
    | 10.01. |           0.0 |         1.0 |   0.004547 |                   0.0 |                0.02 |              0.02 | 0.105263 |              0.694398 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.105263 |      0.048078 |            0.054461 |            0.0 | 0.048078 |    0.018189 |           0.0 |      0.054461 |            0.0 | 0.105263 | 0.048078 |        0.784979 |
    | 11.01. |           0.0 |         5.0 |   0.003114 |                   0.0 |               0.084 |             0.084 | 0.094737 |              0.784979 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.094737 |      0.034284 |            0.042796 |            0.0 | 0.034284 |    0.012456 |           0.0 |      0.042796 |            0.0 | 0.094737 | 0.034284 |         0.81852 |
    | 12.01. |           0.0 |         5.0 |   0.001877 |                   0.0 |              0.0968 |          0.096767 | 0.084211 |               0.81852 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.084211 |      0.019723 |            0.024987 |            0.0 | 0.019723 |    0.007509 |           0.0 |      0.024987 |            0.0 | 0.084211 | 0.019723 |        0.840207 |
    | 13.01. |           0.0 |         5.0 |   0.000812 |                   0.0 |             0.09936 |           0.09629 | 0.073684 |              0.840207 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.073684 |      0.011381 |            0.015318 |            0.0 | 0.011381 |    0.003249 |           0.0 |      0.015318 |            0.0 | 0.073684 | 0.011381 |         0.72592 |
    | 14.01. |           0.0 |         5.0 |   0.000133 |                   0.0 |            0.099872 |          0.079215 | 0.063158 |               0.72592 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.063158 |      0.006741 |            0.008625 |            0.0 | 0.006741 |    0.000534 |           0.0 |      0.008625 |            0.0 | 0.063158 | 0.006741 |        0.575373 |
    | 15.01. |           0.0 |         5.0 |  -0.000084 |                   0.0 |            0.099974 |          0.052067 | 0.052632 |              0.575373 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.052632 |      0.004844 |            0.005803 |            0.0 | 0.004844 |   -0.000337 |           0.0 |      0.005803 |            0.0 | 0.052632 | 0.004844 |        0.386003 |
    | 16.01. |           0.0 |         5.0 |  -0.000067 |                   0.0 |            0.099995 |          0.034075 | 0.042105 |              0.386003 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.042105 |      0.003618 |            0.003613 |            0.0 | 0.003618 |   -0.000268 |           0.0 |      0.003613 |            0.0 | 0.042105 | 0.003618 |        0.198088 |
    | 17.01. |           0.0 |         5.0 |  -0.000256 |                   0.0 |            0.099999 |          0.035719 | 0.031579 |              0.198088 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.031579 |      0.002733 |            0.001868 |            0.0 | 0.002733 |   -0.001023 |           0.0 |      0.001868 |            0.0 | 0.031579 | 0.002733 |        0.113577 |
    | 18.01. |           0.0 |         5.0 |  -0.000281 |                   0.0 |                 0.1 |          0.019524 | 0.021053 |              0.113577 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.021053 |      0.001686 |            0.000985 |            0.0 | 0.001686 |   -0.001122 |           0.0 |      0.000985 |            0.0 | 0.021053 | 0.001686 |         0.05798 |
    | 19.01. |           0.0 |         5.0 |  -0.000394 |                   0.0 |                 0.1 |           0.01451 | 0.010526 |               0.05798 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.010526 |      0.000808 |            0.000481 |            0.0 | 0.000808 |   -0.001578 |           0.0 |      0.000481 |            0.0 | 0.010526 | 0.000808 |        0.026921 |
    | 20.01. |           0.0 |         5.0 |  -0.000592 |                   0.0 |                 0.1 |          0.008923 |      0.0 |              0.026921 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.0 |           0.0 |             0.00021 |            0.0 |      0.0 |   -0.002367 |           0.0 |       0.00021 |            0.0 |      0.0 |      0.0 |             0.0 |

.. _dam_v004_flood_retention:

flood retention
_______________

The following examples correspond to the :ref:`dam_v001_flood_retention` example of
application model |dam_v001| as well as the :ref:`dam_v003_flood_retention` example
of application model |dam_v003|.  We use the same parameter and input time series
configuration:

>>> neardischargeminimumthreshold(0.0)
>>> neardischargeminimumtolerance(0.0)
>>> waterlevelminimumthreshold(0.0)
>>> waterlevelminimumtolerance(0.0)
>>> waterlevelminimumremotethreshold(0.0)
>>> waterlevelminimumremotetolerance(0.0)
>>> waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 2.5]))
>>> neardischargeminimumthreshold(0.0)
>>> inputs.precipitation.series = [0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inflow.sequences.sim.series = [0.0, 0.0, 5.0, 9.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.0,
...                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> inputs.evaporation.series = 0.0


.. _dam_v004_flood_retention_recalculation:

recalculation
-------------

To first perform a strict recalculation, we set the remote demand to zero (the allowed
relief is already zero):

>>> required_supply.sequences.sim.series = 0.0
>>> test.inits.loggedrequiredremoterelease = 0.0
>>> allowed_relief.sequences.sim.series   # doctest: +ELLIPSIS
InfoArray([0., ..., 0.])

The following results demonstrate that |dam_v003| calculates the same outflow values as
|dam_v001| and |dam_v003| in situations where the remote locations are inactive:

.. integration-test::

    >>> test("dam_v004_flood_retention_recalculation")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |        0.0 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |            0.0 |      0.0 |         0.0 |           0.0 |           0.0 |            0.0 |    0.0 |      0.0 |             0.0 |
    | 02.01. |          50.0 |         0.0 |   0.021027 |                   1.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.026514 | 0.026514 |    0.084109 |           0.0 |           0.0 |            0.0 |    0.0 | 0.026514 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.125058 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.183744 | 0.183744 |    0.500234 |           0.0 |           0.0 |            0.0 |    5.0 | 0.183744 |             0.0 |
    | 04.01. |           0.0 |         0.0 |    0.30773 |                   0.0 |                 0.0 |               0.0 |    9.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.542983 | 0.542983 |     1.23092 |           0.0 |           0.0 |            0.0 |    9.0 | 0.542983 |             0.0 |
    | 05.01. |           0.0 |         0.0 |   0.459772 |                   0.0 |                 0.0 |               0.0 |    8.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.961039 | 0.961039 |    1.839086 |           0.0 |           0.0 |            0.0 |    8.0 | 0.961039 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.540739 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.251523 | 1.251523 |    2.162955 |           0.0 |           0.0 |            0.0 |    5.0 | 1.251523 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.575395 |                   0.0 |                 0.0 |               0.0 |    3.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.395546 | 1.395546 |    2.301579 |           0.0 |           0.0 |            0.0 |    3.0 | 1.395546 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.587202 |                   0.0 |                 0.0 |               0.0 |    2.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.453375 | 1.453375 |    2.348808 |           0.0 |           0.0 |            0.0 |    2.0 | 1.453375 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.577361 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.455596 | 1.455596 |    2.309444 |           0.0 |           0.0 |            0.0 |    1.0 | 1.455596 |             0.0 |
    | 10.01. |           0.0 |         0.0 |    0.54701 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.405132 | 1.405132 |    2.188041 |           0.0 |           0.0 |            0.0 |    0.0 | 1.405132 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.518255 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.331267 | 1.331267 |    2.073019 |           0.0 |           0.0 |            0.0 |    0.0 | 1.331267 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.491011 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.261285 | 1.261285 |    1.964044 |           0.0 |           0.0 |            0.0 |    0.0 | 1.261285 |             0.0 |
    | 13.01. |           0.0 |         0.0 |     0.4652 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.194981 | 1.194981 |    1.860798 |           0.0 |           0.0 |            0.0 |    0.0 | 1.194981 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.440745 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.132163 | 1.132163 |    1.762979 |           0.0 |           0.0 |            0.0 |    0.0 | 1.132163 |             0.0 |
    | 15.01. |           0.0 |         0.0 |   0.417576 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.072647 | 1.072647 |    1.670302 |           0.0 |           0.0 |            0.0 |    0.0 | 1.072647 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.395624 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.01626 |  1.01626 |    1.582498 |           0.0 |           0.0 |            0.0 |    0.0 |  1.01626 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.374827 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.962837 | 0.962837 |    1.499308 |           0.0 |           0.0 |            0.0 |    0.0 | 0.962837 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.355123 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.912222 | 0.912222 |    1.420492 |           0.0 |           0.0 |            0.0 |    0.0 | 0.912222 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.336455 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.864268 | 0.864268 |     1.34582 |           0.0 |           0.0 |            0.0 |    0.0 | 0.864268 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.318768 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.818835 | 0.818835 |    1.275072 |           0.0 |           0.0 |            0.0 |    0.0 | 0.818835 |             0.0 |

.. _dam_v004_flood_retention_modification:

modification
------------

Building on the example above, we demonstrate the possibility to constrain the total
discharge to remote locations by setting |HighestRemoteDischarge| to 1.0 m³/s, which
defines the allowed sum of |AllowedRemoteRelief| and |ActualRemoteRelease|:

>>> highestremotedischarge(1.0)
>>> highestremotetolerance(0.1)

This final example demonstrates the identical behaviour of models
|dam_v003| and |dam_v004| (and also of models |dam_v001| and
|dam_v002| regarding high flow conditions:

We assume a constant remote demand of 0.5 m³/s and let the allowed relief rise linearly
from 0.0 to 1.5 m³/s:

>>> required_supply.sequences.sim.series = 0.5
>>> test.inits.loggedrequiredremoterelease = 0.5
>>> allowed_relief.sequences.sim.series = numpy.linspace(0.0, 1.5, 20)
>>> test.inits.loggedallowedremoterelief = 0.0

Also, we set the possible relief discharge to a constant value of 5.0 m³/s:

>>> waterlevel2possibleremoterelief(PPoly.from_data(xs=[0.0], ys=[5.0]))
>>> figure = waterlevel2possibleremoterelief.plot(-0.1, 1.0)
>>> save_autofig("dam_v004_waterlevel2possibleremoterelief_4.png", figure=figure)

.. image:: dam_v004_waterlevel2possibleremoterelief_4.png
   :width: 400

The following results demonstrate that |AllowedRemoteRelief| has priority over
|ActualRemoteRelease|. Due to parameter |HighestRemoteDischarge| set to 1.0 m³/s,
|ActualRemoteRelease| starts to drop when |AllowedRemoteRelief| exceeds 0.5 m³/s.
Furthermore, |AllowedRemoteRelief| itself never exceeds 1.0 m³/s:

.. integration-test::

    >>> test("dam_v004_flood_retention_modification")
    |   date | precipitation | evaporation | waterlevel | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | requiredremoterelease | allowedremoterelief | possibleremoterelief | actualremoterelief | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relief | actual_supply | allowed_relief | inflow |  outflow | required_supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           0.0 |         0.0 |   -0.00027 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |                 0.0 |                  5.0 |                0.0 |             0.0 |             0.0 |           0.0 |              0.0125 |      -0.001125 |      0.0 |    -0.00108 |           0.0 |        0.0125 |            0.0 |    0.0 |      0.0 |             0.5 |
    | 02.01. |          50.0 |         0.0 |    0.01059 |                   1.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |                 0.0 |                  5.0 |                0.0 |             0.0 |             0.0 |           0.0 |            0.483321 |       0.013893 | 0.013915 |    0.042359 |           0.0 |      0.483321 |       0.078947 |    0.0 | 0.013915 |             0.5 |
    | 03.01. |           0.0 |         0.0 |   0.102997 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.5 |            0.078947 |                  5.0 |           0.078947 |             0.0 |             0.0 |           0.0 |            0.499952 |       0.142993 | 0.142993 |    0.411987 |      0.078947 |      0.499952 |       0.157895 |    5.0 | 0.142993 |             0.5 |
    | 04.01. |           0.0 |         0.0 |   0.272998 |                   0.0 |                 0.0 |               0.0 |    9.0 |                   0.5 |            0.157895 |                  5.0 |           0.157895 |             0.0 |             0.0 |           0.0 |            0.499819 |       0.471852 | 0.471852 |    1.091993 |      0.157895 |      0.499819 |       0.236842 |    9.0 | 0.471852 |             0.5 |
    | 05.01. |           0.0 |         0.0 |   0.411386 |                   0.0 |                 0.0 |               0.0 |    8.0 |                   0.5 |            0.236842 |                  5.0 |           0.236842 |             0.0 |             0.0 |           0.0 |            0.499314 |       0.856993 | 0.856993 |    1.645545 |      0.236842 |      0.499314 |       0.315789 |    8.0 | 0.856993 |             0.5 |
    | 06.01. |           0.0 |         0.0 |   0.477797 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.5 |            0.315789 |                  5.0 |           0.315789 |             0.0 |             0.0 |           0.0 |            0.497434 |       1.112205 | 1.112205 |    1.911188 |      0.315789 |      0.497434 |       0.394737 |    5.0 | 1.112205 |             0.5 |
    | 07.01. |           0.0 |         0.0 |   0.497142 |                   0.0 |                 0.0 |               0.0 |    3.0 |                   0.5 |            0.394737 |                  5.0 |           0.394735 |             0.0 |             0.0 |           0.0 |            0.490789 |       1.218885 | 1.218885 |    1.988567 |      0.394735 |      0.490789 |       0.473684 |    3.0 | 1.218885 |             0.5 |
    | 08.01. |           0.0 |         0.0 |   0.493206 |                   0.0 |                 0.0 |               0.0 |    2.0 |                   0.5 |            0.473684 |                  5.0 |           0.473676 |             0.0 |             0.0 |           0.0 |            0.470723 |       1.237798 | 1.237798 |    1.972825 |      0.473676 |      0.470723 |       0.552632 |    2.0 | 1.237798 |             0.5 |
    | 09.01. |           0.0 |         0.0 |   0.467708 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.5 |            0.552632 |                  5.0 |           0.552601 |             0.0 |             0.0 |           0.0 |            0.427028 |       1.200864 | 1.200864 |     1.87083 |      0.552601 |      0.427028 |       0.631579 |    1.0 | 1.200864 |             0.5 |
    | 10.01. |           0.0 |         0.0 |   0.422227 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.631579 |                  5.0 |           0.631463 |             0.0 |             0.0 |           0.0 |            0.362181 |       1.111921 | 1.111921 |     1.68891 |      0.631463 |      0.362181 |       0.710526 |    0.0 | 1.111921 |             0.5 |
    | 11.01. |           0.0 |         0.0 |   0.379068 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.710526 |                  5.0 |           0.710086 |             0.0 |             0.0 |           0.0 |            0.286864 |       1.001148 | 1.001148 |    1.516274 |      0.710086 |      0.286864 |       0.789474 |    0.0 | 1.001148 |             0.5 |
    | 12.01. |           0.0 |         0.0 |   0.338188 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.789474 |                  5.0 |           0.787817 |             0.0 |             0.0 |           0.0 |            0.208657 |       0.896124 | 0.896124 |    1.352753 |      0.787817 |      0.208657 |       0.868421 |    0.0 | 0.896124 |             0.5 |
    | 13.01. |           0.0 |         0.0 |   0.299546 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.868421 |                  5.0 |           0.862356 |             0.0 |             0.0 |           0.0 |            0.129881 |       0.796746 | 0.796746 |    1.198185 |      0.862356 |      0.129881 |       0.947368 |    0.0 | 0.796746 |             0.5 |
    | 14.01. |           0.0 |         0.0 |   0.263233 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.947368 |                  5.0 |           0.927029 |             0.0 |             0.0 |           0.0 |            0.051045 |       0.703078 | 0.703078 |    1.052934 |      0.927029 |      0.051045 |       1.026316 |    0.0 | 0.703078 |             0.5 |
    | 15.01. |           0.0 |         0.0 |   0.228984 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.026316 |                  5.0 |           0.970723 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.614897 | 0.614897 |    0.915936 |      0.970723 |           0.0 |       1.105263 |    0.0 | 0.614897 |             0.5 |
    | 16.01. |           0.0 |         0.0 |   0.196114 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.105263 |                  5.0 |           0.990741 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.531013 | 0.531013 |    0.784457 |      0.990741 |           0.0 |       1.184211 |    0.0 | 0.531013 |             0.5 |
    | 17.01. |           0.0 |         0.0 |   0.164846 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.184211 |                  5.0 |           0.996746 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.450858 | 0.450858 |    0.659384 |      0.996746 |           0.0 |       1.263158 |    0.0 | 0.450858 |             0.5 |
    | 18.01. |           0.0 |         0.0 |   0.135195 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.263158 |                  5.0 |           0.997993 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.374727 | 0.374727 |    0.540781 |      0.997993 |           0.0 |       1.342105 |    0.0 | 0.374727 |             0.5 |
    | 19.01. |           0.0 |         0.0 |   0.107097 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.342105 |                  5.0 |           0.998268 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.302558 | 0.302558 |    0.428389 |      0.998268 |           0.0 |       1.421053 |    0.0 | 0.302558 |             0.5 |
    | 20.01. |           0.0 |         0.0 |   0.080475 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.421053 |                  5.0 |           0.998337 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.234174 | 0.234174 |      0.3219 |      0.998337 |           0.0 |            1.5 |    0.0 | 0.234174 |             0.5 |
"""

# import...
# ...from HydPy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(modeltools.ELSModel):
    """Version 4 of HydPy-Dam."""

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
        dam_model.Calc_RequiredRemoteRelease_V2,
        dam_model.Calc_AllowedRemoteRelief_V1,
        dam_model.Calc_RequiredRelease_V2,
        dam_model.Calc_TargetedRelease_V1,
    )
    RECEIVER_METHODS = (
        dam_model.Pic_LoggedRequiredRemoteRelease_V2,
        dam_model.Pic_LoggedAllowedRemoteRelief_V1,
    )
    ADD_METHODS = (dam_model.Fix_Min1_V1,)
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_ActualRelease_V1,
        dam_model.Calc_PossibleRemoteRelief_V1,
        dam_model.Calc_ActualRemoteRelief_V1,
        dam_model.Calc_ActualRemoteRelease_V1,
        dam_model.Update_ActualRemoteRelease_V1,
        dam_model.Update_ActualRemoteRelief_V1,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_Outflow_V1,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V3,)
    OUTLET_METHODS = (
        dam_model.Calc_WaterLevel_V1,
        dam_model.Pass_Outflow_V1,
        dam_model.Pass_ActualRemoteRelease_V1,
        dam_model.Pass_ActualRemoteRelief_V1,
    )
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
