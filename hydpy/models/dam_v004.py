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
    | 01.01. |           0.0 |         0.0 |   0.017174 |                   0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.199917 |            0.004998 |            0.0 | 0.199917 |    0.068695 |           0.0 |      0.004998 |            0.0 |    1.0 | 0.199917 |        0.008588 |
    | 02.01. |           0.0 |         0.0 |   0.034268 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008588 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.008588 |            0.0 |      0.2 |    0.137073 |           0.0 |      0.008588 |            0.0 |    1.0 |      0.2 |        0.010053 |
    | 03.01. |           0.0 |         0.0 |   0.051331 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.010053 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.010053 |            0.0 |      0.2 |    0.205325 |           0.0 |      0.010053 |            0.0 |    1.0 |      0.2 |        0.013858 |
    | 04.01. |           0.0 |         0.0 |   0.068312 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.013858 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.013858 |            0.0 |      0.2 |    0.273247 |           0.0 |      0.013858 |            0.0 |    1.0 |      0.2 |        0.027322 |
    | 05.01. |           0.0 |         0.0 |   0.085002 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.027322 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.027322 |            0.0 |      0.2 |    0.340007 |           0.0 |      0.027322 |            0.0 |    1.0 |      0.2 |        0.064075 |
    | 06.01. |           0.0 |         0.0 |   0.100898 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.064075 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.064075 |            0.0 |      0.2 |    0.403591 |           0.0 |      0.064075 |            0.0 |    1.0 |      0.2 |        0.235523 |
    | 07.01. |           0.0 |         0.0 |    0.11309 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.235523 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.235523 |            0.0 |      0.2 |    0.452362 |           0.0 |      0.235523 |            0.0 |    1.0 |      0.2 |        0.470414 |
    | 08.01. |           0.0 |         0.0 |   0.120209 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.470414 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.470414 |            0.0 |      0.2 |    0.480838 |           0.0 |      0.470414 |            0.0 |    1.0 |      0.2 |        0.735001 |
    | 09.01. |           0.0 |         0.0 |   0.121613 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.735001 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.735001 |            0.0 |      0.2 |    0.486454 |           0.0 |      0.735001 |            0.0 |    1.0 |      0.2 |        0.891263 |
    | 10.01. |           0.0 |         0.0 |   0.119642 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.891263 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.891263 |            0.0 |      0.2 |    0.478569 |           0.0 |      0.891263 |            0.0 |    1.0 |      0.2 |        0.696325 |
    | 11.01. |           0.0 |         0.0 |   0.121882 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.696325 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.696325 |            0.0 |      0.2 |    0.487526 |           0.0 |      0.696325 |            0.0 |    1.0 |      0.2 |        0.349797 |
    | 12.01. |           0.0 |         0.0 |   0.131606 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.349797 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.349797 |            0.0 |      0.2 |    0.526424 |           0.0 |      0.349797 |            0.0 |    1.0 |      0.2 |        0.105231 |
    | 13.01. |           0.0 |         0.0 |   0.146613 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.105231 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.105231 |            0.0 |      0.2 |    0.586452 |           0.0 |      0.105231 |            0.0 |    1.0 |      0.2 |        0.111928 |
    | 14.01. |           0.0 |         0.0 |   0.161475 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.111928 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.111928 |            0.0 |      0.2 |    0.645901 |           0.0 |      0.111928 |            0.0 |    1.0 |      0.2 |        0.240436 |
    | 15.01. |           0.0 |         0.0 |   0.173562 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.240436 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.240436 |            0.0 |      0.2 |    0.694247 |           0.0 |      0.240436 |            0.0 |    1.0 |      0.2 |        0.229369 |
    | 16.01. |           0.0 |         0.0 |   0.185887 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.229369 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.229369 |            0.0 |      0.2 |     0.74355 |           0.0 |      0.229369 |            0.0 |    1.0 |      0.2 |        0.058622 |
    | 17.01. |           0.0 |         0.0 |   0.201901 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.058622 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.058622 |            0.0 |      0.2 |    0.807605 |           0.0 |      0.058622 |            0.0 |    1.0 |      0.2 |        0.016958 |
    | 18.01. |           0.0 |         0.0 |   0.218815 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.016958 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.016958 |            0.0 |      0.2 |     0.87526 |           0.0 |      0.016958 |            0.0 |    1.0 |      0.2 |        0.008447 |
    | 19.01. |           0.0 |         0.0 |   0.235913 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008447 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.008447 |            0.0 |      0.2 |     0.94365 |           0.0 |      0.008447 |            0.0 |    1.0 |      0.2 |        0.004155 |
    | 20.01. |           0.0 |         0.0 |   0.253103 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.004155 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.004155 |            0.0 |      0.2 |    1.012411 |           0.0 |      0.004155 |            0.0 |    1.0 |      0.2 |             0.0 |

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
    | 01.01. |           0.0 |         0.0 |   0.017174 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |               0.005 |                100.0 |              0.005 |             0.2 |             0.2 |      0.199917 |                 0.0 |            0.0 | 0.199917 |    0.068695 |         0.005 |           0.0 |       0.008588 |    1.0 | 0.199917 |             0.0 |
    | 02.01. |           0.0 |         0.0 |   0.034268 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008588 |                100.0 |           0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137073 |      0.008588 |           0.0 |       0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.051331 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.010053 |                100.0 |           0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.205325 |      0.010053 |           0.0 |       0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |           0.0 |         0.0 |   0.068312 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.013858 |                100.0 |           0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.273247 |      0.013858 |           0.0 |       0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |           0.0 |         0.0 |   0.085002 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.027322 |                100.0 |           0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340007 |      0.027322 |           0.0 |       0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.100898 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.064075 |                100.0 |           0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.403591 |      0.064075 |           0.0 |       0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |           0.0 |         0.0 |    0.11309 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.235523 |                100.0 |           0.235523 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.452361 |      0.235523 |           0.0 |       0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.120209 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.470414 |                100.0 |           0.470414 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.480838 |      0.470414 |           0.0 |       0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.121613 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.735001 |                100.0 |           0.735001 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.486454 |      0.735001 |           0.0 |       0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |           0.0 |         0.0 |   0.119642 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.891263 |                100.0 |           0.891263 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.478568 |      0.891263 |           0.0 |       0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.121881 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.696325 |                100.0 |           0.696325 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.487526 |      0.696325 |           0.0 |       0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.131606 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.349797 |                100.0 |           0.349797 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.526423 |      0.349797 |           0.0 |       0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |           0.0 |         0.0 |   0.146613 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.105231 |                100.0 |           0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.586452 |      0.105231 |           0.0 |       0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.161475 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.111928 |                100.0 |           0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.645901 |      0.111928 |           0.0 |       0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |           0.0 |         0.0 |   0.173562 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.240436 |                100.0 |           0.240436 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.694247 |      0.240436 |           0.0 |       0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.185887 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.229369 |                100.0 |           0.229369 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.74355 |      0.229369 |           0.0 |       0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.201901 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.058622 |                100.0 |           0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.807605 |      0.058622 |           0.0 |       0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.218815 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.016958 |                100.0 |           0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.87526 |      0.016958 |           0.0 |       0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.235912 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008447 |                100.0 |           0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.94365 |      0.008447 |           0.0 |       0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.253103 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.004155 |                100.0 |           0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.012411 |      0.004155 |           0.0 |            0.0 |    1.0 |      0.2 |             0.0 |

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
    | 01.01. |           0.0 |         0.0 |   0.017174 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |               0.005 |                  0.5 |              0.005 |             0.2 |             0.2 |      0.199917 |                 0.0 |            0.0 | 0.199917 |    0.068695 |         0.005 |           0.0 |       0.008588 |    1.0 | 0.199917 |             0.0 |
    | 02.01. |           0.0 |         0.0 |   0.034268 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008588 |                  0.5 |           0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137073 |      0.008588 |           0.0 |       0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.051331 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.010053 |                  0.5 |           0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.205325 |      0.010053 |           0.0 |       0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |           0.0 |         0.0 |   0.068312 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.013858 |                  0.5 |           0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.273247 |      0.013858 |           0.0 |       0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |           0.0 |         0.0 |   0.085002 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.027322 |                  0.5 |           0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340007 |      0.027322 |           0.0 |       0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.100898 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.064075 |                  0.5 |           0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.403591 |      0.064075 |           0.0 |       0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |           0.0 |         0.0 |    0.11309 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.235523 |                  0.5 |           0.235523 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.452361 |      0.235523 |           0.0 |       0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.120209 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.470414 |                  0.5 |           0.470414 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.480838 |      0.470414 |           0.0 |       0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.126689 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.735001 |                  0.5 |                0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.506758 |           0.5 |           0.0 |       0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |           0.0 |         0.0 |   0.133169 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.891263 |                  0.5 |                0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.532678 |           0.5 |           0.0 |       0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.139649 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.696325 |                  0.5 |                0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.558598 |           0.5 |           0.0 |       0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.149374 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.349797 |                  0.5 |           0.349797 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.597495 |      0.349797 |           0.0 |       0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |           0.0 |         0.0 |   0.164381 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.105231 |                  0.5 |           0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.657523 |      0.105231 |           0.0 |       0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.179243 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.111928 |                  0.5 |           0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.716973 |      0.111928 |           0.0 |       0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |           0.0 |         0.0 |    0.19133 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.240436 |                  0.5 |           0.240436 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.765319 |      0.240436 |           0.0 |       0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.203655 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.229369 |                  0.5 |           0.229369 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.814621 |      0.229369 |           0.0 |       0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.219669 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.058622 |                  0.5 |           0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.878677 |      0.058622 |           0.0 |       0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.236583 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.016958 |                  0.5 |           0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.946331 |      0.016958 |           0.0 |       0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |           0.0 |         0.0 |    0.25368 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008447 |                  0.5 |           0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.014722 |      0.008447 |           0.0 |       0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.270871 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.004155 |                  0.5 |           0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.083483 |      0.004155 |           0.0 |            0.0 |    1.0 |      0.2 |             0.0 |

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
    | 01.01. |           0.0 |         0.0 |   0.017174 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |               0.005 |                  0.5 |              0.005 |             0.2 |             0.2 |      0.199917 |                 0.0 |            0.0 | 0.199917 |    0.068695 |         0.005 |           0.0 |       0.008588 |    1.0 | 0.199917 |             0.0 |
    | 02.01. |           0.0 |         0.0 |   0.034268 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008588 |                  0.5 |           0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137073 |      0.008588 |           0.0 |       0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.051331 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.010053 |                  0.5 |           0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.205325 |      0.010053 |           0.0 |       0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |           0.0 |         0.0 |   0.068312 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.013858 |                  0.5 |           0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.273247 |      0.013858 |           0.0 |       0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |           0.0 |         0.0 |   0.085002 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.027322 |                  0.5 |           0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340007 |      0.027322 |           0.0 |       0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.100898 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.064075 |                  0.5 |           0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.403591 |      0.064075 |           0.0 |       0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.113094 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.235523 |                  0.5 |           0.235352 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.452376 |      0.235352 |           0.0 |       0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.121327 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.470414 |                  0.5 |           0.418836 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.485309 |      0.418836 |           0.0 |       0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.128393 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.735001 |                  0.5 |           0.472874 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.513572 |      0.472874 |           0.0 |       0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |           0.0 |         0.0 |    0.13529 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.891263 |                  0.5 |           0.480688 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.541161 |      0.480688 |           0.0 |       0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.142428 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.696325 |                  0.5 |           0.469547 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.569712 |      0.469547 |           0.0 |       0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.152319 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.349797 |                  0.5 |           0.342067 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.609278 |      0.342067 |           0.0 |       0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |           0.0 |         0.0 |   0.167326 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.105231 |                  0.5 |           0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.669306 |      0.105231 |           0.0 |       0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.182189 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.111928 |                  0.5 |           0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.728755 |      0.111928 |           0.0 |       0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |           0.0 |         0.0 |    0.19428 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.240436 |                  0.5 |           0.240219 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.77712 |      0.240219 |           0.0 |       0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.206608 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.229369 |                  0.5 |           0.229243 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.826434 |      0.229243 |           0.0 |       0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.222622 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.058622 |                  0.5 |           0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.890489 |      0.058622 |           0.0 |       0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.239536 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.016958 |                  0.5 |           0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.958143 |      0.016958 |           0.0 |       0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.256633 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.008447 |                  0.5 |           0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.026534 |      0.008447 |           0.0 |       0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.273824 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |            0.004155 |                  0.5 |           0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.095295 |      0.004155 |           0.0 |            0.0 |    1.0 |      0.2 |             0.0 |

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
    | 01.01. |           0.0 |         0.0 |   0.017174 |                   0.0 |                 0.0 |               0.0 |    1.0 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.199917 |            0.004998 |            0.0 | 0.199917 |    0.068695 |           0.0 |      0.004998 |            0.0 |    1.0 | 0.199917 |        0.008746 |
    | 02.01. |           0.0 |         0.0 |   0.034265 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.008746 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.008746 |            0.0 |      0.2 |     0.13706 |           0.0 |      0.008746 |            0.0 |    1.0 |      0.2 |        0.010632 |
    | 03.01. |           0.0 |         0.0 |   0.051315 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.010632 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.010632 |            0.0 |      0.2 |    0.205261 |           0.0 |      0.010632 |            0.0 |    1.0 |      0.2 |        0.015099 |
    | 04.01. |           0.0 |         0.0 |   0.068269 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.015099 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.015099 |            0.0 |      0.2 |    0.273077 |           0.0 |      0.015099 |            0.0 |    1.0 |      0.2 |         0.03006 |
    | 05.01. |           0.0 |         0.0 |     0.0849 |                   0.0 |                 0.0 |               0.0 |    1.0 |               0.03006 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |             0.03006 |            0.0 |      0.2 |    0.339599 |           0.0 |       0.03006 |            0.0 |    1.0 |      0.2 |        0.068641 |
    | 06.01. |           0.0 |         0.0 |   0.100697 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.068641 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.068641 |            0.0 |      0.2 |    0.402789 |           0.0 |      0.068641 |            0.0 |    1.0 |      0.2 |        0.242578 |
    | 07.01. |           0.0 |         0.0 |   0.112738 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.242578 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.242578 |            0.0 |      0.2 |     0.45095 |           0.0 |      0.242578 |            0.0 |    1.0 |      0.2 |        0.474285 |
    | 08.01. |           0.0 |         0.0 |   0.119773 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.474285 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.474285 |            0.0 |      0.2 |    0.479092 |           0.0 |      0.474285 |            0.0 |    1.0 |      0.2 |        0.784512 |
    | 09.01. |           0.0 |         0.0 |   0.120108 |                   0.0 |                 0.0 |               0.0 |    1.0 |              0.784512 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |            0.784512 |            0.0 |      0.2 |     0.48043 |           0.0 |      0.784512 |            0.0 |    1.0 |      0.2 |         0.95036 |
    | 10.01. |           0.0 |         0.0 |    0.11686 |                   0.0 |                 0.0 |               0.0 |    1.0 |               0.95036 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |           0.2 |             0.95036 |            0.0 |      0.2 |    0.467439 |           0.0 |       0.95036 |            0.0 |    1.0 |      0.2 |            0.35 |
    | 11.01. |           0.0 |         0.0 |     0.1093 |                   0.0 |                 0.0 |               0.0 |    0.1 |                  0.35 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |                0.35 |            0.0 |      0.1 |    0.437199 |           0.0 |          0.35 |            0.0 |    0.1 |      0.1 |        0.034564 |
    | 12.01. |           0.0 |         0.0 |   0.108553 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.034564 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.034564 |            0.0 |      0.1 |    0.434213 |           0.0 |      0.034564 |            0.0 |    0.1 |      0.1 |        0.299482 |
    | 13.01. |           0.0 |         0.0 |   0.102084 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.299482 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.299482 |            0.0 |      0.1 |    0.408337 |           0.0 |      0.299482 |            0.0 |    0.1 |      0.1 |        0.585979 |
    | 14.01. |           0.0 |         0.0 |   0.089427 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.585979 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.585979 |            0.0 |      0.1 |    0.357709 |           0.0 |      0.585979 |            0.0 |    0.1 |      0.1 |        0.557422 |
    | 15.01. |           0.0 |         0.0 |   0.077387 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.557422 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.557422 |            0.0 |      0.1 |    0.309547 |           0.0 |      0.557422 |            0.0 |    0.1 |      0.1 |        0.229369 |
    | 16.01. |           0.0 |         0.0 |   0.072432 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.229369 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.229369 |            0.0 |      0.1 |     0.28973 |           0.0 |      0.229369 |            0.0 |    0.1 |      0.1 |        0.142578 |
    | 17.01. |           0.0 |         0.0 |   0.069353 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.142578 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.142578 |            0.0 |      0.1 |    0.277411 |           0.0 |      0.142578 |            0.0 |    0.1 |      0.1 |        0.068641 |
    | 18.01. |           0.0 |         0.0 |    0.06787 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.068641 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.068641 |            0.0 |      0.1 |    0.271481 |           0.0 |      0.068641 |            0.0 |    0.1 |      0.1 |        0.029844 |
    | 19.01. |           0.0 |         0.0 |   0.067226 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.029844 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.029844 |            0.0 |      0.1 |    0.268902 |           0.0 |      0.029844 |            0.0 |    0.1 |      0.1 |        0.012348 |
    | 20.01. |           0.0 |         0.0 |   0.066959 |                   0.0 |                 0.0 |               0.0 |    0.1 |              0.012348 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.1 |           0.1 |            0.012348 |            0.0 |      0.1 |    0.267835 |           0.0 |      0.012348 |            0.0 |    0.1 |      0.1 |             0.0 |

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
    | 01.01. |           0.0 |         0.0 |   0.003462 |                   0.0 |                 0.0 |               0.0 |      0.2 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.039605 |            0.000125 |            0.0 | 0.039605 |    0.013847 |           0.0 |      0.000125 |            0.0 |      0.2 | 0.039605 |         0.01232 |
    | 02.01. |           0.0 |         0.0 |   0.005651 |                   0.0 |                 0.0 |               0.0 | 0.189474 |               0.01232 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.189474 |       0.08713 |            0.000999 |            0.0 |  0.08713 |    0.022604 |           0.0 |      0.000999 |            0.0 | 0.189474 |  0.08713 |        0.029323 |
    | 03.01. |           0.0 |         0.0 |   0.006915 |                   0.0 |                 0.0 |               0.0 | 0.178947 |              0.029323 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.178947 |      0.115815 |            0.004617 |            0.0 | 0.115815 |    0.027659 |           0.0 |      0.004617 |            0.0 | 0.178947 | 0.115815 |        0.064084 |
    | 04.01. |           0.0 |         0.0 |    0.00756 |                   0.0 |                 0.0 |               0.0 | 0.168421 |              0.064084 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.168421 |      0.124349 |            0.014199 |            0.0 | 0.124349 |     0.03024 |           0.0 |      0.014199 |            0.0 | 0.168421 | 0.124349 |        0.120198 |
    | 05.01. |           0.0 |         0.0 |    0.00769 |                   0.0 |                 0.0 |               0.0 | 0.157895 |              0.120198 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.157895 |      0.121593 |            0.030276 |            0.0 | 0.121593 |    0.030761 |           0.0 |      0.030276 |            0.0 | 0.157895 | 0.121593 |        0.247367 |
    | 06.01. |           0.0 |         0.0 |   0.007221 |                   0.0 |                 0.0 |               0.0 | 0.147368 |              0.247367 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.147368 |      0.110974 |            0.058113 |            0.0 | 0.110974 |    0.028885 |           0.0 |      0.058113 |            0.0 | 0.147368 | 0.110974 |         0.45567 |
    | 07.01. |           0.0 |         0.0 |   0.006355 |                   0.0 |                 0.0 |               0.0 | 0.136842 |               0.45567 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.136842 |      0.094052 |            0.082892 |            0.0 | 0.094052 |     0.02542 |           0.0 |      0.082892 |            0.0 | 0.136842 | 0.094052 |        0.608464 |
    | 08.01. |           0.0 |         0.0 |   0.005656 |                   0.0 |                 0.0 |               0.0 | 0.126316 |              0.608464 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.126316 |      0.076665 |            0.082026 |            0.0 | 0.076665 |    0.022622 |           0.0 |      0.082026 |            0.0 | 0.126316 | 0.076665 |        0.537314 |
    | 09.01. |           0.0 |         0.0 |   0.005435 |                   0.0 |                 0.0 |               0.0 | 0.115789 |              0.537314 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.115789 |      0.064915 |            0.061095 |            0.0 | 0.064915 |    0.021739 |           0.0 |      0.061095 |            0.0 | 0.115789 | 0.064915 |        0.629775 |
    | 10.01. |           0.0 |         0.0 |   0.005122 |                   0.0 |                 0.0 |               0.0 | 0.105263 |              0.629775 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.105263 |      0.055735 |            0.064032 |            0.0 | 0.055735 |    0.020486 |           0.0 |      0.064032 |            0.0 | 0.105263 | 0.055735 |        0.744091 |
    | 11.01. |           0.0 |         0.0 |    0.00475 |                   0.0 |                 0.0 |               0.0 | 0.094737 |              0.744091 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.094737 |        0.0464 |            0.065527 |            0.0 |   0.0464 |    0.019001 |           0.0 |      0.065527 |            0.0 | 0.094737 |   0.0464 |         0.82219 |
    | 12.01. |           0.0 |         0.0 |   0.004406 |                   0.0 |                 0.0 |               0.0 | 0.084211 |               0.82219 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.084211 |      0.037828 |            0.062332 |            0.0 | 0.037828 |    0.017623 |           0.0 |      0.062332 |            0.0 | 0.084211 | 0.037828 |        0.841916 |
    | 13.01. |           0.0 |         0.0 |   0.004127 |                   0.0 |                 0.0 |               0.0 | 0.073684 |              0.841916 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.073684 |      0.030563 |             0.05601 |            0.0 | 0.030563 |    0.016509 |           0.0 |       0.05601 |            0.0 | 0.073684 | 0.030563 |        0.701812 |
    | 14.01. |           0.0 |         0.0 |   0.004021 |                   0.0 |                 0.0 |               0.0 | 0.063158 |              0.701812 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.063158 |      0.024926 |            0.043161 |            0.0 | 0.024926 |    0.016084 |           0.0 |      0.043161 |            0.0 | 0.063158 | 0.024926 |        0.533258 |
    | 15.01. |           0.0 |         0.0 |   0.004021 |                   0.0 |                 0.0 |               0.0 | 0.052632 |              0.533258 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.052632 |      0.020495 |            0.032121 |            0.0 | 0.020495 |    0.016085 |           0.0 |      0.032121 |            0.0 | 0.052632 | 0.020495 |        0.351863 |
    | 16.01. |           0.0 |         0.0 |   0.004106 |                   0.0 |                 0.0 |               0.0 | 0.042105 |              0.351863 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.042105 |      0.016599 |            0.021602 |            0.0 | 0.016599 |    0.016422 |           0.0 |      0.021602 |            0.0 | 0.042105 | 0.016599 |        0.185207 |
    | 17.01. |           0.0 |         0.0 |   0.004252 |                   0.0 |                 0.0 |               0.0 | 0.031579 |              0.185207 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.031579 |      0.012852 |            0.011952 |            0.0 | 0.012852 |    0.017008 |           0.0 |      0.011952 |            0.0 | 0.031579 | 0.012852 |        0.107697 |
    | 18.01. |           0.0 |         0.0 |   0.004357 |                   0.0 |                 0.0 |               0.0 | 0.021053 |              0.107697 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.021053 |      0.008861 |            0.007331 |            0.0 | 0.008861 |    0.017428 |           0.0 |      0.007331 |            0.0 | 0.021053 | 0.008861 |        0.055458 |
    | 19.01. |           0.0 |         0.0 |   0.004402 |                   0.0 |                 0.0 |               0.0 | 0.010526 |              0.055458 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.010526 |      0.004519 |            0.003898 |            0.0 | 0.004519 |     0.01761 |           0.0 |      0.003898 |            0.0 | 0.010526 | 0.004519 |        0.025948 |
    | 20.01. |           0.0 |         0.0 |   0.004363 |                   0.0 |                 0.0 |               0.0 |      0.0 |              0.025948 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.0 |           0.0 |            0.001826 |            0.0 |      0.0 |    0.017452 |           0.0 |      0.001826 |            0.0 |      0.0 |      0.0 |             0.0 |

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
    | 01.01. |           0.0 |         1.0 |   0.003181 |                   0.0 |               0.016 |          0.015347 |      0.2 |                 0.005 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.2 |      0.037276 |            0.000116 |            0.0 | 0.037276 |    0.012723 |           0.0 |      0.000116 |            0.0 |      0.2 | 0.037276 |        0.012321 |
    | 02.01. |           0.0 |         1.0 |   0.005144 |                   0.0 |              0.0192 |            0.0192 | 0.189474 |              0.012321 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.189474 |      0.078569 |            0.000837 |            0.0 | 0.078569 |    0.020574 |           0.0 |      0.000837 |            0.0 | 0.189474 | 0.078569 |        0.029352 |
    | 03.01. |           0.0 |         1.0 |   0.006246 |                   0.0 |             0.01984 |           0.01984 | 0.178947 |              0.029352 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.178947 |      0.104408 |            0.003653 |            0.0 | 0.104408 |    0.024985 |           0.0 |      0.003653 |            0.0 | 0.178947 | 0.104408 |        0.064305 |
    | 04.01. |           0.0 |         1.0 |   0.006783 |                   0.0 |            0.019968 |          0.019968 | 0.168421 |              0.064305 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.168421 |      0.112714 |             0.01089 |            0.0 | 0.112714 |    0.027132 |           0.0 |       0.01089 |            0.0 | 0.168421 | 0.112714 |        0.120897 |
    | 05.01. |           0.0 |         1.0 |   0.006882 |                   0.0 |            0.019994 |          0.019994 | 0.157895 |              0.120897 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.157895 |      0.110416 |            0.022906 |            0.0 | 0.110416 |    0.027527 |           0.0 |      0.022906 |            0.0 | 0.157895 | 0.110416 |        0.248435 |
    | 06.01. |           0.0 |         1.0 |   0.006503 |                   0.0 |            0.019999 |          0.019999 | 0.147368 |              0.248435 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.147368 |       0.10065 |            0.044264 |            0.0 |  0.10065 |    0.026011 |           0.0 |      0.044264 |            0.0 | 0.147368 |  0.10065 |        0.453671 |
    | 07.01. |           0.0 |         1.0 |   0.005786 |                   0.0 |                0.02 |              0.02 | 0.136842 |              0.453671 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.136842 |      0.085218 |            0.064794 |            0.0 | 0.085218 |    0.023146 |           0.0 |      0.064794 |            0.0 | 0.136842 | 0.085218 |        0.585089 |
    | 08.01. |           0.0 |         1.0 |   0.005189 |                   0.0 |                0.02 |              0.02 | 0.126316 |              0.585089 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.126316 |      0.069588 |            0.064373 |            0.0 | 0.069588 |    0.020757 |           0.0 |      0.064373 |            0.0 | 0.126316 | 0.069588 |        0.550583 |
    | 09.01. |           0.0 |         1.0 |   0.004901 |                   0.0 |                0.02 |              0.02 | 0.115789 |              0.550583 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.115789 |      0.058259 |            0.050888 |            0.0 | 0.058259 |    0.019603 |           0.0 |      0.050888 |            0.0 | 0.115789 | 0.058259 |        0.694398 |
    | 10.01. |           0.0 |         1.0 |   0.004496 |                   0.0 |                0.02 |              0.02 | 0.105263 |              0.694398 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.105263 |      0.048686 |            0.055331 |            0.0 | 0.048686 |    0.017983 |           0.0 |      0.055331 |            0.0 | 0.105263 | 0.048686 |        0.784979 |
    | 11.01. |           0.0 |         5.0 |   0.003086 |                   0.0 |               0.084 |             0.084 | 0.094737 |              0.784979 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.094737 |      0.033924 |            0.042097 |            0.0 | 0.033924 |    0.012342 |           0.0 |      0.042097 |            0.0 | 0.094737 | 0.033924 |         0.81852 |
    | 12.01. |           0.0 |         5.0 |   0.001849 |                   0.0 |              0.0968 |          0.096796 | 0.084211 |               0.81852 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.084211 |       0.01987 |            0.024773 |            0.0 |  0.01987 |    0.007398 |           0.0 |      0.024773 |            0.0 | 0.084211 |  0.01987 |        0.840207 |
    | 13.01. |           0.0 |         5.0 |    0.00074 |                   0.0 |             0.09936 |          0.098662 | 0.073684 |              0.840207 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.073684 |       0.01131 |            0.015082 |            0.0 |  0.01131 |    0.002959 |           0.0 |      0.015082 |            0.0 | 0.073684 |  0.01131 |         0.72592 |
    | 14.01. |           0.0 |         5.0 |   0.000083 |                   0.0 |            0.099872 |          0.078473 | 0.063158 |               0.72592 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.063158 |      0.006629 |            0.008462 |            0.0 | 0.006629 |    0.000332 |           0.0 |      0.008462 |            0.0 | 0.063158 | 0.006629 |        0.575373 |
    | 15.01. |           0.0 |         5.0 |  -0.000055 |                   0.0 |            0.099974 |          0.048539 | 0.052632 |              0.575373 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.052632 |      0.004782 |            0.005722 |            0.0 | 0.004782 |   -0.000222 |           0.0 |      0.005722 |            0.0 | 0.052632 | 0.004782 |        0.386003 |
    | 16.01. |           0.0 |         5.0 |  -0.000129 |                   0.0 |            0.099995 |          0.038137 | 0.042105 |              0.386003 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.042105 |      0.003679 |            0.003679 |            0.0 | 0.003679 |   -0.000515 |           0.0 |      0.003679 |            0.0 | 0.042105 | 0.003679 |        0.198088 |
    | 17.01. |           0.0 |         5.0 |  -0.000204 |                   0.0 |            0.099999 |          0.030567 | 0.031579 |              0.198088 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.031579 |      0.002676 |            0.001826 |            0.0 | 0.002676 |   -0.000816 |           0.0 |      0.001826 |            0.0 | 0.031579 | 0.002676 |        0.113577 |
    | 18.01. |           0.0 |         5.0 |  -0.000301 |                   0.0 |                 0.1 |          0.022795 | 0.021053 |              0.113577 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.021053 |      0.001719 |            0.001006 |            0.0 | 0.001719 |   -0.001202 |           0.0 |      0.001006 |            0.0 | 0.021053 | 0.001719 |         0.05798 |
    | 19.01. |           0.0 |         5.0 |  -0.000428 |                   0.0 |                 0.1 |          0.015126 | 0.010526 |               0.05798 |                 0.0 |                  0.0 |                0.0 |             0.2 |        0.010526 |       0.00082 |            0.000488 |            0.0 |  0.00082 |   -0.001713 |           0.0 |      0.000488 |            0.0 | 0.010526 |  0.00082 |        0.026921 |
    | 20.01. |           0.0 |         5.0 |  -0.000609 |                   0.0 |                 0.1 |          0.008146 |      0.0 |              0.026921 |                 0.0 |                  0.0 |                0.0 |             0.2 |             0.0 |           0.0 |            0.000211 |            0.0 |      0.0 |   -0.002435 |           0.0 |      0.000211 |            0.0 |      0.0 |      0.0 |             0.0 |

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
    | 02.01. |          50.0 |         0.0 |   0.021027 |                   1.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.026521 | 0.026521 |    0.084109 |           0.0 |           0.0 |            0.0 |    0.0 | 0.026521 |             0.0 |
    | 03.01. |           0.0 |         0.0 |   0.125058 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.183777 | 0.183777 |     0.50023 |           0.0 |           0.0 |            0.0 |    5.0 | 0.183777 |             0.0 |
    | 04.01. |           0.0 |         0.0 |   0.307728 |                   0.0 |                 0.0 |               0.0 |    9.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.543038 | 0.543038 |    1.230912 |           0.0 |           0.0 |            0.0 |    9.0 | 0.543038 |             0.0 |
    | 05.01. |           0.0 |         0.0 |   0.459769 |                   0.0 |                 0.0 |               0.0 |    8.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.961082 | 0.961082 |    1.839074 |           0.0 |           0.0 |            0.0 |    8.0 | 0.961082 |             0.0 |
    | 06.01. |           0.0 |         0.0 |   0.540735 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.251541 | 1.251541 |    2.162941 |           0.0 |           0.0 |            0.0 |    5.0 | 1.251541 |             0.0 |
    | 07.01. |           0.0 |         0.0 |   0.575391 |                   0.0 |                 0.0 |               0.0 |    3.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.395548 | 1.395548 |    2.301566 |           0.0 |           0.0 |            0.0 |    3.0 | 1.395548 |             0.0 |
    | 08.01. |           0.0 |         0.0 |   0.587199 |                   0.0 |                 0.0 |               0.0 |    2.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.453371 | 1.453371 |    2.348795 |           0.0 |           0.0 |            0.0 |    2.0 | 1.453371 |             0.0 |
    | 09.01. |           0.0 |         0.0 |   0.577358 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.455585 | 1.455585 |    2.309432 |           0.0 |           0.0 |            0.0 |    1.0 | 1.455585 |             0.0 |
    | 10.01. |           0.0 |         0.0 |   0.547008 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.405115 | 1.405115 |     2.18803 |           0.0 |           0.0 |            0.0 |    0.0 | 1.405115 |             0.0 |
    | 11.01. |           0.0 |         0.0 |   0.518253 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.331251 | 1.331251 |     2.07301 |           0.0 |           0.0 |            0.0 |    0.0 | 1.331251 |             0.0 |
    | 12.01. |           0.0 |         0.0 |   0.491009 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.26127 |  1.26127 |    1.964036 |           0.0 |           0.0 |            0.0 |    0.0 |  1.26127 |             0.0 |
    | 13.01. |           0.0 |         0.0 |   0.465198 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.194968 | 1.194968 |    1.860791 |           0.0 |           0.0 |            0.0 |    0.0 | 1.194968 |             0.0 |
    | 14.01. |           0.0 |         0.0 |   0.440743 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.132151 | 1.132151 |    1.762973 |           0.0 |           0.0 |            0.0 |    0.0 | 1.132151 |             0.0 |
    | 15.01. |           0.0 |         0.0 |   0.417574 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.072636 | 1.072636 |    1.670297 |           0.0 |           0.0 |            0.0 |    0.0 | 1.072636 |             0.0 |
    | 16.01. |           0.0 |         0.0 |   0.395623 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.01625 |  1.01625 |    1.582493 |           0.0 |           0.0 |            0.0 |    0.0 |  1.01625 |             0.0 |
    | 17.01. |           0.0 |         0.0 |   0.374826 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.962828 | 0.962828 |    1.499305 |           0.0 |           0.0 |            0.0 |    0.0 | 0.962828 |             0.0 |
    | 18.01. |           0.0 |         0.0 |   0.355122 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.912214 | 0.912214 |     1.42049 |           0.0 |           0.0 |            0.0 |    0.0 | 0.912214 |             0.0 |
    | 19.01. |           0.0 |         0.0 |   0.336454 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.864261 | 0.864261 |    1.345818 |           0.0 |           0.0 |            0.0 |    0.0 | 0.864261 |             0.0 |
    | 20.01. |           0.0 |         0.0 |   0.318768 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.0 |                 0.0 |                  0.0 |                0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.818829 | 0.818829 |    1.275071 |           0.0 |           0.0 |            0.0 |    0.0 | 0.818829 |             0.0 |

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
    | 01.01. |           0.0 |         0.0 |  -0.000003 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |                 0.0 |                  5.0 |                0.0 |             0.0 |             0.0 |           0.0 |            0.000125 |      -0.000007 |      0.0 |   -0.000011 |           0.0 |      0.000125 |            0.0 |    0.0 |      0.0 |             0.5 |
    | 02.01. |          50.0 |         0.0 |   0.010515 |                   1.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |                 0.0 |                  5.0 |                0.0 |             0.0 |             0.0 |           0.0 |            0.499821 |       0.013263 | 0.013263 |    0.042059 |           0.0 |      0.499821 |       0.078947 |    0.0 | 0.013263 |             0.5 |
    | 03.01. |           0.0 |         0.0 |   0.102925 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.5 |            0.078947 |                  5.0 |           0.078947 |             0.0 |             0.0 |           0.0 |            0.499952 |        0.14284 |  0.14284 |      0.4117 |      0.078947 |      0.499952 |       0.157895 |    5.0 |  0.14284 |             0.5 |
    | 04.01. |           0.0 |         0.0 |   0.272929 |                   0.0 |                 0.0 |               0.0 |    9.0 |                   0.5 |            0.157895 |                  5.0 |           0.157895 |             0.0 |             0.0 |           0.0 |            0.499819 |       0.471731 | 0.471731 |    1.091717 |      0.157895 |      0.499819 |       0.236842 |    9.0 | 0.471731 |             0.5 |
    | 05.01. |           0.0 |         0.0 |    0.41132 |                   0.0 |                 0.0 |               0.0 |    8.0 |                   0.5 |            0.236842 |                  5.0 |           0.236842 |             0.0 |             0.0 |           0.0 |            0.499314 |       0.856868 | 0.856868 |    1.645279 |      0.236842 |      0.499314 |       0.315789 |    8.0 | 0.856868 |             0.5 |
    | 06.01. |           0.0 |         0.0 |   0.477734 |                   0.0 |                 0.0 |               0.0 |    5.0 |                   0.5 |            0.315789 |                  5.0 |           0.315789 |             0.0 |             0.0 |           0.0 |            0.497434 |       1.112064 | 1.112064 |    1.910934 |      0.315789 |      0.497434 |       0.394737 |    5.0 | 1.112064 |             0.5 |
    | 07.01. |           0.0 |         0.0 |   0.497082 |                   0.0 |                 0.0 |               0.0 |    3.0 |                   0.5 |            0.394737 |                  5.0 |           0.394735 |             0.0 |             0.0 |           0.0 |            0.490789 |       1.218737 | 1.218737 |    1.988326 |      0.394735 |      0.490789 |       0.473684 |    3.0 | 1.218737 |             0.5 |
    | 08.01. |           0.0 |         0.0 |   0.493147 |                   0.0 |                 0.0 |               0.0 |    2.0 |                   0.5 |            0.473684 |                  5.0 |           0.473676 |             0.0 |             0.0 |           0.0 |            0.470723 |       1.237743 | 1.237743 |    1.972589 |      0.473676 |      0.470723 |       0.552632 |    2.0 | 1.237743 |             0.5 |
    | 09.01. |           0.0 |         0.0 |   0.467652 |                   0.0 |                 0.0 |               0.0 |    1.0 |                   0.5 |            0.552632 |                  5.0 |           0.552601 |             0.0 |             0.0 |           0.0 |            0.427028 |       1.200712 | 1.200712 |    1.870608 |      0.552601 |      0.427028 |       0.631579 |    1.0 | 1.200712 |             0.5 |
    | 10.01. |           0.0 |         0.0 |   0.422175 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.631579 |                  5.0 |           0.631463 |             0.0 |             0.0 |           0.0 |            0.362181 |       1.111772 | 1.111772 |      1.6887 |      0.631463 |      0.362181 |       0.710526 |    0.0 | 1.111772 |             0.5 |
    | 11.01. |           0.0 |         0.0 |   0.379019 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.710526 |                  5.0 |           0.710086 |             0.0 |             0.0 |           0.0 |            0.286864 |       1.001007 | 1.001007 |    1.516076 |      0.710086 |      0.286864 |       0.789474 |    0.0 | 1.001007 |             0.5 |
    | 12.01. |           0.0 |         0.0 |   0.338142 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.789474 |                  5.0 |           0.787817 |             0.0 |             0.0 |           0.0 |            0.208657 |       0.895991 | 0.895991 |    1.352567 |      0.787817 |      0.208657 |       0.868421 |    0.0 | 0.895991 |             0.5 |
    | 13.01. |           0.0 |         0.0 |   0.299503 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.868421 |                  5.0 |           0.862356 |             0.0 |             0.0 |           0.0 |            0.129881 |       0.796621 | 0.796621 |     1.19801 |      0.862356 |      0.129881 |       0.947368 |    0.0 | 0.796621 |             0.5 |
    | 14.01. |           0.0 |         0.0 |   0.263192 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            0.947368 |                  5.0 |           0.927029 |             0.0 |             0.0 |           0.0 |            0.051045 |        0.70296 |  0.70296 |    1.052769 |      0.927029 |      0.051045 |       1.026316 |    0.0 |  0.70296 |             0.5 |
    | 15.01. |           0.0 |         0.0 |   0.228945 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.026316 |                  5.0 |           0.970723 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.614786 | 0.614786 |    0.915781 |      0.970723 |           0.0 |       1.105263 |    0.0 | 0.614786 |             0.5 |
    | 16.01. |           0.0 |         0.0 |   0.196078 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.105263 |                  5.0 |           0.990741 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.530909 | 0.530909 |     0.78431 |      0.990741 |           0.0 |       1.184211 |    0.0 | 0.530909 |             0.5 |
    | 17.01. |           0.0 |         0.0 |   0.164811 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.184211 |                  5.0 |           0.996746 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.450759 | 0.450759 |    0.659246 |      0.996746 |           0.0 |       1.263158 |    0.0 | 0.450759 |             0.5 |
    | 18.01. |           0.0 |         0.0 |   0.135163 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.263158 |                  5.0 |           0.997993 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.374634 | 0.374634 |    0.540651 |      0.997993 |           0.0 |       1.342105 |    0.0 | 0.374634 |             0.5 |
    | 19.01. |           0.0 |         0.0 |   0.107067 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.342105 |                  5.0 |           0.998268 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.302471 | 0.302471 |    0.428267 |      0.998268 |           0.0 |       1.421053 |    0.0 | 0.302471 |             0.5 |
    | 20.01. |           0.0 |         0.0 |   0.080446 |                   0.0 |                 0.0 |               0.0 |    0.0 |                   0.5 |            1.421053 |                  5.0 |           0.998337 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.234092 | 0.234092 |    0.321785 |      0.998337 |           0.0 |            1.5 |    0.0 | 0.234092 |             0.5 |
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
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
