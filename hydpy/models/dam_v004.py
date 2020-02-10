# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Version 4 of HydPy-Dam

    Application model |dam_v004| is an extension if model |dam_v003|.
    Both models are able to discharge water into the channel downstream
    and to remote locations.  The difference is that |dam_v003|
    can discharge water only to a single remote location, e.g. to a
    drinking water treatment plant, while |dam_v004| is also able to
    discharge water to a separate remote location independently, e.g.
    to relieve water during high flow conditions.

    Integration examples:

    The following examples are based on the ones of application model
    |dam_v003|, which in turn are taken from the documentation on
    application model |dam_v001|.  So please follow the links for more
    detailed explanations.

    :ref:`Exact recalculation of example 7 <dam_v003_ex07>`

    In addition to the general configuration of application model
    |dam_v003|, two additional node connections are required:
    one node is supposed to provide the information on the maximum
    allowed relieve discharge, and the other one is supposed to pass
    the actual relieve discharge to a remote location. For both
    nodes handle the variable `R`, while nodes `required_suppy` and
    `actual_supply` still handle variable `S`:

    >>> from hydpy import pub, Node, Element
    >>> pub.timegrids = '01.01.2000', '21.01.2000', '1d'
    >>> inflow = Node('inflow', variable='Q')
    >>> required_supply = Node('required_supply', variable='S')
    >>> allowed_relieve = Node('allowed_relieve', variable='R')
    >>> outflow = Node('release', variable='Q')
    >>> actual_supply = Node('actual_supply', variable='S')
    >>> actual_relieve = Node('actual_relieve', variable='R')
    >>> dam = Element('dam',
    ...               inlets=inflow,
    ...               outlets=(outflow, actual_supply, actual_relieve),
    ...               receivers=(required_supply, allowed_relieve))
    >>> from hydpy.models.dam_v004 import *
    >>> parameterstep('1d')
    >>> dam.model = model

    The first test calculation is supposed to show that model |dam_v004|
    behaves exactly like model |dam_v003| when the relieve discharge is
    disabled, which can be accomplished by the following settings:

    >>> from hydpy import IntegrationTest
    >>> IntegrationTest.plotting_options.activated=(
    ...     fluxes.inflow, fluxes.outflow)
    >>> test = IntegrationTest(
    ...     dam,
    ...     inits=((states.watervolume, 0.0),
    ...            (logs.loggedrequiredremoterelease, 0.005),
    ...            (logs.loggedallowedremoterelieve, 0.0)))
    >>> test.dateformat = '%d.%m.'
    >>> inflow.sequences.sim.series = 1.0
    >>> required_supply.sequences.sim.series = [
    ...     0.008588, 0.010053, 0.013858, 0.027322, 0.064075,
    ...     0.235523, 0.470414, 0.735001, 0.891263, 0.696325,
    ...     0.349797, 0.105231, 0.111928, 0.240436, 0.229369,
    ...     0.058622, 0.016958, 0.008447, 0.004155, 0.0]
    >>> allowed_relieve.sequences.sim.series = 0.0
    >>> watervolume2waterlevel(
    ...         weights_input=1e-6, weights_output=1e6,
    ...         intercepts_hidden=0.0, intercepts_output=-1e6/2)
    >>> waterlevel2flooddischarge(ann(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=0.0))
    >>> catchmentarea(86.4)
    >>> neardischargeminimumthreshold(0.2)
    >>> neardischargeminimumtolerance(0.2)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)
    >>> waterlevelminimumremotethreshold(0.0)
    >>> waterlevelminimumremotetolerance(0.0)
    >>> waterlevel2possibleremoterelieve(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=0.0)
    >>> remoterelievetolerance(0.0)
    >>> highestremotedischarge(inf)
    >>> highestremotetolerance(0.1)
    >>> restricttargetedrelease(True)
    >>> parameters.update()

    Comparing the results of the following table with the ones shown for
    application model |dam_v004| (e.g. of column `waterlevel` or
    `actualremoterelease`) shows that both models can in fact be
    functionally identical:

    >>> test('dam_v004_ex7')
    |   date | inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve | inflow |  release | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                 0.005 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 |            0.0 |      0.004792 |             0.0 |    1.0 | 0.191667 |        0.008588 |
    | 02.01. |    1.0 |              0.008588 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.008588 |            0.0 |      0.2 |    0.137804 |            0.0 |      0.008588 |             0.0 |    1.0 |      0.2 |        0.010053 |
    | 03.01. |    1.0 |              0.010053 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.010053 |            0.0 |      0.2 |    0.206055 |            0.0 |      0.010053 |             0.0 |    1.0 |      0.2 |        0.013858 |
    | 04.01. |    1.0 |              0.013858 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.013858 |            0.0 |      0.2 |    0.273978 |            0.0 |      0.013858 |             0.0 |    1.0 |      0.2 |        0.027322 |
    | 05.01. |    1.0 |              0.027322 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.027322 |            0.0 |      0.2 |    0.340737 |            0.0 |      0.027322 |             0.0 |    1.0 |      0.2 |        0.064075 |
    | 06.01. |    1.0 |              0.064075 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.064075 |            0.0 |      0.2 |    0.404321 |            0.0 |      0.064075 |             0.0 |    1.0 |      0.2 |        0.235523 |
    | 07.01. |    1.0 |              0.235523 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.235523 |            0.0 |      0.2 |    0.453092 |            0.0 |      0.235523 |             0.0 |    1.0 |      0.2 |        0.470414 |
    | 08.01. |    1.0 |              0.470414 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.470414 |            0.0 |      0.2 |    0.481568 |            0.0 |      0.470414 |             0.0 |    1.0 |      0.2 |        0.735001 |
    | 09.01. |    1.0 |              0.735001 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.735001 |            0.0 |      0.2 |    0.487184 |            0.0 |      0.735001 |             0.0 |    1.0 |      0.2 |        0.891263 |
    | 10.01. |    1.0 |              0.891263 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.891263 |            0.0 |      0.2 |    0.479299 |            0.0 |      0.891263 |             0.0 |    1.0 |      0.2 |        0.696325 |
    | 11.01. |    1.0 |              0.696325 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.696325 |            0.0 |      0.2 |    0.488257 |            0.0 |      0.696325 |             0.0 |    1.0 |      0.2 |        0.349797 |
    | 12.01. |    1.0 |              0.349797 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.349797 |            0.0 |      0.2 |    0.527154 |            0.0 |      0.349797 |             0.0 |    1.0 |      0.2 |        0.105231 |
    | 13.01. |    1.0 |              0.105231 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.105231 |            0.0 |      0.2 |    0.587182 |            0.0 |      0.105231 |             0.0 |    1.0 |      0.2 |        0.111928 |
    | 14.01. |    1.0 |              0.111928 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.111928 |            0.0 |      0.2 |    0.646632 |            0.0 |      0.111928 |             0.0 |    1.0 |      0.2 |        0.240436 |
    | 15.01. |    1.0 |              0.240436 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.240436 |            0.0 |      0.2 |    0.694978 |            0.0 |      0.240436 |             0.0 |    1.0 |      0.2 |        0.229369 |
    | 16.01. |    1.0 |              0.229369 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.229369 |            0.0 |      0.2 |    0.744281 |            0.0 |      0.229369 |             0.0 |    1.0 |      0.2 |        0.058622 |
    | 17.01. |    1.0 |              0.058622 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.058622 |            0.0 |      0.2 |    0.808336 |            0.0 |      0.058622 |             0.0 |    1.0 |      0.2 |        0.016958 |
    | 18.01. |    1.0 |              0.016958 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.016958 |            0.0 |      0.2 |     0.87599 |            0.0 |      0.016958 |             0.0 |    1.0 |      0.2 |        0.008447 |
    | 19.01. |    1.0 |              0.008447 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.008447 |            0.0 |      0.2 |    0.944381 |            0.0 |      0.008447 |             0.0 |    1.0 |      0.2 |        0.004155 |
    | 20.01. |    1.0 |              0.004155 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.004155 |            0.0 |      0.2 |    1.013142 |            0.0 |      0.004155 |             0.0 |    1.0 |      0.2 |             0.0 |

    .. raw:: html

        <iframe
            src="dam_v004_ex7.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>

    :ref:`First modification of example 7 <dam_v003_ex07>`

    In this first modification of the example above, the "old" required
    supply is taken as the "new" allowed relieve discharge and the "new"
    required supply is set to zero.  Also, the possible relieve discharge
    is set to a very large value (100 m³/s):

    >>> test.inits.loggedrequiredremoterelease = 0.0
    >>> test.inits.loggedallowedremoterelieve = 0.005
    >>> allowed_relieve.sequences.sim.series = (
    ...     required_supply.sequences.sim.series)
    >>> required_supply.sequences.sim.series = 0.0
    >>> waterlevel2possibleremoterelieve(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=100.0)
    >>> waterlevel2possibleremoterelieve.plot(-0.1, 1.0)

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> pyplot.close()

    Due to this setting, the "new" actual relieve discharge is nearly
    identical with the "old" actual supply discharge.  There is only
    a small deviation on the first timestep, which is due to a numerical
    inaccuracy, which is explained in the documentation on application
    model |dam_v001|:

    >>> test('dam_v004_ex7_1')
    |   date | inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve | inflow |  release | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                   0.0 |                0.005 |                 100.0 |               0.005 |             0.2 |             0.2 |      0.191667 |                 0.0 |            0.0 | 0.191667 |    0.069408 |          0.005 |           0.0 |        0.008588 |    1.0 | 0.191667 |             0.0 |
    | 02.01. |    1.0 |                   0.0 |             0.008588 |                 100.0 |            0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137786 |       0.008588 |           0.0 |        0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |    1.0 |                   0.0 |             0.010053 |                 100.0 |            0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.206037 |       0.010053 |           0.0 |        0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |    1.0 |                   0.0 |             0.013858 |                 100.0 |            0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.27396 |       0.013858 |           0.0 |        0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |    1.0 |                   0.0 |             0.027322 |                 100.0 |            0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340719 |       0.027322 |           0.0 |        0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |    1.0 |                   0.0 |             0.064075 |                 100.0 |            0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.404303 |       0.064075 |           0.0 |        0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |    1.0 |                   0.0 |             0.235523 |                 100.0 |            0.235523 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.453074 |       0.235523 |           0.0 |        0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |    1.0 |                   0.0 |             0.470414 |                 100.0 |            0.470414 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.48155 |       0.470414 |           0.0 |        0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |    1.0 |                   0.0 |             0.735001 |                 100.0 |            0.735001 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.487166 |       0.735001 |           0.0 |        0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |    1.0 |                   0.0 |             0.891263 |                 100.0 |            0.891263 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.479281 |       0.891263 |           0.0 |        0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |    1.0 |                   0.0 |             0.696325 |                 100.0 |            0.696325 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.488239 |       0.696325 |           0.0 |        0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |    1.0 |                   0.0 |             0.349797 |                 100.0 |            0.349797 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.527136 |       0.349797 |           0.0 |        0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |    1.0 |                   0.0 |             0.105231 |                 100.0 |            0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.587164 |       0.105231 |           0.0 |        0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |    1.0 |                   0.0 |             0.111928 |                 100.0 |            0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.646614 |       0.111928 |           0.0 |        0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |    1.0 |                   0.0 |             0.240436 |                 100.0 |            0.240436 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.69496 |       0.240436 |           0.0 |        0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |    1.0 |                   0.0 |             0.229369 |                 100.0 |            0.229369 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.744263 |       0.229369 |           0.0 |        0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |    1.0 |                   0.0 |             0.058622 |                 100.0 |            0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.808318 |       0.058622 |           0.0 |        0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |    1.0 |                   0.0 |             0.016958 |                 100.0 |            0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.875972 |       0.016958 |           0.0 |        0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |    1.0 |                   0.0 |             0.008447 |                 100.0 |            0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.944363 |       0.008447 |           0.0 |        0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |    1.0 |                   0.0 |             0.004155 |                 100.0 |            0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.013124 |       0.004155 |           0.0 |             0.0 |    1.0 |      0.2 |             0.0 |

    .. raw:: html

        <iframe
            src="dam_v004_ex7_1.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>

    :ref:`Second modification of example 7 <dam_v003_ex07>`

    Now we modify the artificial neuronal network
    |WaterLevel2PossibleRemoteRelieve| (in fact, only a single neuron)
    in order to prevent any relieve discharge when the dam is emtpy and
    to set maximum relieve discharge of 0.5 m³/s:

    >>> waterlevel2possibleremoterelieve(
    ...        weights_input=1e30, weights_output=0.5,
    ...        intercepts_hidden=-1e27, intercepts_output=0.0)
    >>> waterlevel2possibleremoterelieve.plot(-0.1, 1.0)

    .. testsetup::

        >>> pyplot.close()

    For very small water levels, the new relationship between possible
    relieve discharge an water level resembles the old relationship
    for calculating the actual actual supply release.  Hence, only
    a very small deviation remains at the first simulation timestep.
    The imposed restriction of 0.5 m³/s results in a reduced relieve
    discharge between January, 9, and January, 11:

    >>> test('dam_v004_ex7_2')
    |   date | inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve | inflow |  release | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                   0.0 |                0.005 |              0.483333 |            0.004833 |             0.2 |             0.2 |      0.196667 |                 0.0 |            0.0 | 0.196667 |     0.06899 |       0.004833 |           0.0 |        0.008588 |    1.0 | 0.196667 |             0.0 |
    | 02.01. |    1.0 |                   0.0 |             0.008588 |                   0.5 |            0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137368 |       0.008588 |           0.0 |        0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |    1.0 |                   0.0 |             0.010053 |                   0.5 |            0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.20562 |       0.010053 |           0.0 |        0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |    1.0 |                   0.0 |             0.013858 |                   0.5 |            0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.273542 |       0.013858 |           0.0 |        0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |    1.0 |                   0.0 |             0.027322 |                   0.5 |            0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340302 |       0.027322 |           0.0 |        0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |    1.0 |                   0.0 |             0.064075 |                   0.5 |            0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.403886 |       0.064075 |           0.0 |        0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |    1.0 |                   0.0 |             0.235523 |                   0.5 |            0.235523 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.452657 |       0.235523 |           0.0 |        0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |    1.0 |                   0.0 |             0.470414 |                   0.5 |            0.470414 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.481133 |       0.470414 |           0.0 |        0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |    1.0 |                   0.0 |             0.735001 |                   0.5 |                 0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.507053 |            0.5 |           0.0 |        0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |    1.0 |                   0.0 |             0.891263 |                   0.5 |                 0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.532973 |            0.5 |           0.0 |        0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |    1.0 |                   0.0 |             0.696325 |                   0.5 |                 0.5 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.558893 |            0.5 |           0.0 |        0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |    1.0 |                   0.0 |             0.349797 |                   0.5 |            0.349797 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.59779 |       0.349797 |           0.0 |        0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |    1.0 |                   0.0 |             0.105231 |                   0.5 |            0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.657818 |       0.105231 |           0.0 |        0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |    1.0 |                   0.0 |             0.111928 |                   0.5 |            0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.717268 |       0.111928 |           0.0 |        0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |    1.0 |                   0.0 |             0.240436 |                   0.5 |            0.240436 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.765614 |       0.240436 |           0.0 |        0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |    1.0 |                   0.0 |             0.229369 |                   0.5 |            0.229369 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.814917 |       0.229369 |           0.0 |        0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |    1.0 |                   0.0 |             0.058622 |                   0.5 |            0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.878972 |       0.058622 |           0.0 |        0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |    1.0 |                   0.0 |             0.016958 |                   0.5 |            0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.946627 |       0.016958 |           0.0 |        0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |    1.0 |                   0.0 |             0.008447 |                   0.5 |            0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.015017 |       0.008447 |           0.0 |        0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |    1.0 |                   0.0 |             0.004155 |                   0.5 |            0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.083778 |       0.004155 |           0.0 |             0.0 |    1.0 |      0.2 |             0.0 |

    .. raw:: html

        <iframe
            src="dam_v004_ex7_2.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>

    :ref:`Third modification of example 7 <dam_v003_ex07>`

    The capped possible relieve discharge in the example above results
    in a discontinuous evolution of the actual relieve discharge.  For
    more smooth transitions, the value of parameter |RemoteRelieveTolerance|
    can be set to values larger than zero, e.g.:

    >>> remoterelievetolerance(0.2)
    >>> test('dam_v004_ex7_3')
    |   date | inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve | inflow |  release | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                   0.0 |                0.005 |              0.483333 |            0.004833 |             0.2 |             0.2 |      0.196667 |                 0.0 |            0.0 | 0.196667 |     0.06899 |       0.004833 |           0.0 |        0.008588 |    1.0 | 0.196667 |             0.0 |
    | 02.01. |    1.0 |                   0.0 |             0.008588 |                   0.5 |            0.008588 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.137368 |       0.008588 |           0.0 |        0.010053 |    1.0 |      0.2 |             0.0 |
    | 03.01. |    1.0 |                   0.0 |             0.010053 |                   0.5 |            0.010053 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.20562 |       0.010053 |           0.0 |        0.013858 |    1.0 |      0.2 |             0.0 |
    | 04.01. |    1.0 |                   0.0 |             0.013858 |                   0.5 |            0.013858 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.273542 |       0.013858 |           0.0 |        0.027322 |    1.0 |      0.2 |             0.0 |
    | 05.01. |    1.0 |                   0.0 |             0.027322 |                   0.5 |            0.027322 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.340302 |       0.027322 |           0.0 |        0.064075 |    1.0 |      0.2 |             0.0 |
    | 06.01. |    1.0 |                   0.0 |             0.064075 |                   0.5 |            0.064075 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.403886 |       0.064075 |           0.0 |        0.235523 |    1.0 |      0.2 |             0.0 |
    | 07.01. |    1.0 |                   0.0 |             0.235523 |                   0.5 |            0.235352 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.452671 |       0.235352 |           0.0 |        0.470414 |    1.0 |      0.2 |             0.0 |
    | 08.01. |    1.0 |                   0.0 |             0.470414 |                   0.5 |            0.418836 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.485604 |       0.418836 |           0.0 |        0.735001 |    1.0 |      0.2 |             0.0 |
    | 09.01. |    1.0 |                   0.0 |             0.735001 |                   0.5 |            0.472874 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.513868 |       0.472874 |           0.0 |        0.891263 |    1.0 |      0.2 |             0.0 |
    | 10.01. |    1.0 |                   0.0 |             0.891263 |                   0.5 |            0.480688 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.541456 |       0.480688 |           0.0 |        0.696325 |    1.0 |      0.2 |             0.0 |
    | 11.01. |    1.0 |                   0.0 |             0.696325 |                   0.5 |            0.469547 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.570007 |       0.469547 |           0.0 |        0.349797 |    1.0 |      0.2 |             0.0 |
    | 12.01. |    1.0 |                   0.0 |             0.349797 |                   0.5 |            0.342067 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.609573 |       0.342067 |           0.0 |        0.105231 |    1.0 |      0.2 |             0.0 |
    | 13.01. |    1.0 |                   0.0 |             0.105231 |                   0.5 |            0.105231 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.669601 |       0.105231 |           0.0 |        0.111928 |    1.0 |      0.2 |             0.0 |
    | 14.01. |    1.0 |                   0.0 |             0.111928 |                   0.5 |            0.111928 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     0.72905 |       0.111928 |           0.0 |        0.240436 |    1.0 |      0.2 |             0.0 |
    | 15.01. |    1.0 |                   0.0 |             0.240436 |                   0.5 |            0.240219 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.777415 |       0.240219 |           0.0 |        0.229369 |    1.0 |      0.2 |             0.0 |
    | 16.01. |    1.0 |                   0.0 |             0.229369 |                   0.5 |            0.229243 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.826729 |       0.229243 |           0.0 |        0.058622 |    1.0 |      0.2 |             0.0 |
    | 17.01. |    1.0 |                   0.0 |             0.058622 |                   0.5 |            0.058622 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.890784 |       0.058622 |           0.0 |        0.016958 |    1.0 |      0.2 |             0.0 |
    | 18.01. |    1.0 |                   0.0 |             0.016958 |                   0.5 |            0.016958 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    0.958439 |       0.016958 |           0.0 |        0.008447 |    1.0 |      0.2 |             0.0 |
    | 19.01. |    1.0 |                   0.0 |             0.008447 |                   0.5 |            0.008447 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |    1.026829 |       0.008447 |           0.0 |        0.004155 |    1.0 |      0.2 |             0.0 |
    | 20.01. |    1.0 |                   0.0 |             0.004155 |                   0.5 |            0.004155 |             0.2 |             0.2 |           0.2 |                 0.0 |            0.0 |      0.2 |     1.09559 |       0.004155 |           0.0 |             0.0 |    1.0 |      0.2 |             0.0 |

    .. raw:: html

        <iframe
            src="dam_v004_ex7_3.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>

    :ref:`Exact recalculation of example 8 <dam_v003_ex08>`

    This and the following exact recalculations are just thought to
    prove the identical behaviour of the components models |dam_v003|
    and |dam_v004| that have not been utilised in the examples above.
    Therefore the remote relieve discharge is disabled again:

    >>> test.inits.loggedrequiredremoterelease = 0.005
    >>> test.inits.loggedallowedremoterelieve = 0.0
    >>> waterlevelminimumremotetolerance(0.0)
    >>> waterlevel2possibleremoterelieve(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=0.0)
    >>> remoterelievetolerance(0.0)
    >>> allowed_relieve.sequences.sim.series = 0.0

    Now, the identical behaviour regarding releasing water to the
    channel downstream during low flow conditions is demonstrated:

    >>> inflow.sequences.sim.series[10:] = 0.1
    >>> required_supply.sequences.sim.series = [
    ...     0.008746, 0.010632, 0.015099, 0.03006, 0.068641,
    ...     0.242578, 0.474285, 0.784512, 0.95036, 0.35,
    ...     0.034564, 0.299482, 0.585979, 0.557422, 0.229369,
    ...     0.142578, 0.068641, 0.029844, 0.012348, 0.0]
    >>> neardischargeminimumtolerance(0.0)
    >>> test('dam_v004_ex8')
    |   date | inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve | inflow |  release | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                 0.005 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 |            0.0 |      0.004792 |             0.0 |    1.0 | 0.191667 |        0.008746 |
    | 02.01. |    1.0 |              0.008746 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.008746 |            0.0 |      0.2 |     0.13779 |            0.0 |      0.008746 |             0.0 |    1.0 |      0.2 |        0.010632 |
    | 03.01. |    1.0 |              0.010632 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.010632 |            0.0 |      0.2 |    0.205992 |            0.0 |      0.010632 |             0.0 |    1.0 |      0.2 |        0.015099 |
    | 04.01. |    1.0 |              0.015099 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.015099 |            0.0 |      0.2 |    0.273807 |            0.0 |      0.015099 |             0.0 |    1.0 |      0.2 |         0.03006 |
    | 05.01. |    1.0 |               0.03006 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |             0.03006 |            0.0 |      0.2 |     0.34033 |            0.0 |       0.03006 |             0.0 |    1.0 |      0.2 |        0.068641 |
    | 06.01. |    1.0 |              0.068641 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.068641 |            0.0 |      0.2 |    0.403519 |            0.0 |      0.068641 |             0.0 |    1.0 |      0.2 |        0.242578 |
    | 07.01. |    1.0 |              0.242578 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.242578 |            0.0 |      0.2 |    0.451681 |            0.0 |      0.242578 |             0.0 |    1.0 |      0.2 |        0.474285 |
    | 08.01. |    1.0 |              0.474285 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.474285 |            0.0 |      0.2 |    0.479822 |            0.0 |      0.474285 |             0.0 |    1.0 |      0.2 |        0.784512 |
    | 09.01. |    1.0 |              0.784512 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |            0.784512 |            0.0 |      0.2 |    0.481161 |            0.0 |      0.784512 |             0.0 |    1.0 |      0.2 |         0.95036 |
    | 10.01. |    1.0 |               0.95036 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |           0.2 |             0.95036 |            0.0 |      0.2 |     0.46817 |            0.0 |       0.95036 |             0.0 |    1.0 |      0.2 |            0.35 |
    | 11.01. |    0.1 |                  0.35 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |                0.35 |            0.0 |      0.1 |     0.43793 |            0.0 |          0.35 |             0.0 |    0.1 |      0.1 |        0.034564 |
    | 12.01. |    0.1 |              0.034564 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.034564 |            0.0 |      0.1 |    0.434943 |            0.0 |      0.034564 |             0.0 |    0.1 |      0.1 |        0.299482 |
    | 13.01. |    0.1 |              0.299482 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.299482 |            0.0 |      0.1 |    0.409068 |            0.0 |      0.299482 |             0.0 |    0.1 |      0.1 |        0.585979 |
    | 14.01. |    0.1 |              0.585979 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.585979 |            0.0 |      0.1 |    0.358439 |            0.0 |      0.585979 |             0.0 |    0.1 |      0.1 |        0.557422 |
    | 15.01. |    0.1 |              0.557422 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.557422 |            0.0 |      0.1 |    0.310278 |            0.0 |      0.557422 |             0.0 |    0.1 |      0.1 |        0.229369 |
    | 16.01. |    0.1 |              0.229369 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.229369 |            0.0 |      0.1 |    0.290461 |            0.0 |      0.229369 |             0.0 |    0.1 |      0.1 |        0.142578 |
    | 17.01. |    0.1 |              0.142578 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.142578 |            0.0 |      0.1 |    0.278142 |            0.0 |      0.142578 |             0.0 |    0.1 |      0.1 |        0.068641 |
    | 18.01. |    0.1 |              0.068641 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.068641 |            0.0 |      0.1 |    0.272211 |            0.0 |      0.068641 |             0.0 |    0.1 |      0.1 |        0.029844 |
    | 19.01. |    0.1 |              0.029844 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.029844 |            0.0 |      0.1 |    0.269633 |            0.0 |      0.029844 |             0.0 |    0.1 |      0.1 |        0.012348 |
    | 20.01. |    0.1 |              0.012348 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.1 |           0.1 |            0.012348 |            0.0 |      0.1 |    0.268566 |            0.0 |      0.012348 |             0.0 |    0.1 |      0.1 |             0.0 |

    .. raw:: html

        <iframe
            src="dam_v004_ex8.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>

    :ref:`Exact recalculation of example 10 <dam_v003_ex10>`

    This example demonstates the identical behaviour of models
    |dam_v003| and |dam_v004| regarding limited storage content:

    >>> inflow.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)
    >>> waterlevelminimumtolerance(0.01)
    >>> waterlevelminimumthreshold(0.005)
    >>> waterlevelminimumremotetolerance(0.01)
    >>> waterlevelminimumremotethreshold(0.01)
    >>> required_supply.sequences.sim.series = [
    ...     0.01232, 0.029323, 0.064084, 0.120198, 0.247367,
    ...     0.45567, 0.608464, 0.537314, 0.629775, 0.744091,
    ...     0.82219, 0.841916, 0.701812, 0.533258, 0.351863,
    ...     0.185207, 0.107697, 0.055458, 0.025948, 0.0]
    >>> test('dam_v004_ex10')
    |   date |   inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve |   inflow |  release | required_supply |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |      0.2 |                 0.005 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.2 |      0.038491 |             0.00012 |            0.0 | 0.038491 |    0.013944 |            0.0 |       0.00012 |             0.0 |      0.2 | 0.038491 |         0.01232 |
    | 02.01. | 0.189474 |               0.01232 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.189474 |      0.086988 |            0.000993 |            0.0 | 0.086988 |    0.022713 |            0.0 |      0.000993 |             0.0 | 0.189474 | 0.086988 |        0.029323 |
    | 03.01. | 0.178947 |              0.029323 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.178947 |      0.116103 |            0.004642 |            0.0 | 0.116103 |    0.027742 |            0.0 |      0.004642 |             0.0 | 0.178947 | 0.116103 |        0.064084 |
    | 04.01. | 0.168421 |              0.064084 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.168421 |      0.125159 |            0.014625 |            0.0 | 0.125159 |    0.030216 |            0.0 |      0.014625 |             0.0 | 0.168421 | 0.125159 |        0.120198 |
    | 05.01. | 0.157895 |              0.120198 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.157895 |      0.121681 |            0.030361 |            0.0 | 0.121681 |    0.030722 |            0.0 |      0.030361 |             0.0 | 0.157895 | 0.121681 |        0.247367 |
    | 06.01. | 0.147368 |              0.247367 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.147368 |      0.109923 |            0.056857 |            0.0 | 0.109923 |    0.029044 |            0.0 |      0.056857 |             0.0 | 0.147368 | 0.109923 |         0.45567 |
    | 07.01. | 0.136842 |               0.45567 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.136842 |      0.094858 |            0.084715 |            0.0 | 0.094858 |    0.025352 |            0.0 |      0.084715 |             0.0 | 0.136842 | 0.094858 |        0.608464 |
    | 08.01. | 0.126316 |              0.608464 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.126316 |      0.076914 |            0.082553 |            0.0 | 0.076914 |    0.022488 |            0.0 |      0.082553 |             0.0 | 0.126316 | 0.076914 |        0.537314 |
    | 09.01. | 0.115789 |              0.537314 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.115789 |      0.064167 |            0.059779 |            0.0 | 0.064167 |    0.021783 |            0.0 |      0.059779 |             0.0 | 0.115789 | 0.064167 |        0.629775 |
    | 10.01. | 0.105263 |              0.629775 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.105263 |      0.055154 |            0.063011 |            0.0 | 0.055154 |    0.020669 |            0.0 |      0.063011 |             0.0 | 0.105263 | 0.055154 |        0.744091 |
    | 11.01. | 0.094737 |              0.744091 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.094737 |      0.045986 |            0.064865 |            0.0 | 0.045986 |    0.019277 |            0.0 |      0.064865 |             0.0 | 0.094737 | 0.045986 |         0.82219 |
    | 12.01. | 0.084211 |               0.82219 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.084211 |      0.037699 |             0.06228 |            0.0 | 0.037699 |    0.017914 |            0.0 |       0.06228 |             0.0 | 0.084211 | 0.037699 |        0.841916 |
    | 13.01. | 0.073684 |              0.841916 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.073684 |      0.030632 |            0.056377 |            0.0 | 0.030632 |    0.016763 |            0.0 |      0.056377 |             0.0 | 0.073684 | 0.030632 |        0.701812 |
    | 14.01. | 0.063158 |              0.701812 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.063158 |      0.025166 |            0.043828 |            0.0 | 0.025166 |    0.016259 |            0.0 |      0.043828 |             0.0 | 0.063158 | 0.025166 |        0.533258 |
    | 15.01. | 0.052632 |              0.533258 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.052632 |      0.020693 |            0.032602 |            0.0 | 0.020693 |    0.016201 |            0.0 |      0.032602 |             0.0 | 0.052632 | 0.020693 |        0.351863 |
    | 16.01. | 0.042105 |              0.351863 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.042105 |      0.016736 |            0.021882 |            0.0 | 0.016736 |    0.016502 |            0.0 |      0.021882 |             0.0 | 0.042105 | 0.016736 |        0.185207 |
    | 17.01. | 0.031579 |              0.185207 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.031579 |      0.012934 |            0.012076 |            0.0 | 0.012934 |     0.01707 |            0.0 |      0.012076 |             0.0 | 0.031579 | 0.012934 |        0.107697 |
    | 18.01. | 0.021053 |              0.107697 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.021053 |      0.008901 |            0.007386 |            0.0 | 0.008901 |    0.017482 |            0.0 |      0.007386 |             0.0 | 0.021053 | 0.008901 |        0.055458 |
    | 19.01. | 0.010526 |              0.055458 |                  0.0 |                   0.0 |                 0.0 |             0.2 |        0.010526 |      0.004535 |             0.00392 |            0.0 | 0.004535 |    0.017661 |            0.0 |       0.00392 |             0.0 | 0.010526 | 0.004535 |        0.025948 |
    | 20.01. |      0.0 |              0.025948 |                  0.0 |                   0.0 |                 0.0 |             0.2 |             0.0 |           0.0 |            0.001835 |            0.0 |      0.0 |    0.017502 |            0.0 |      0.001835 |             0.0 |      0.0 |      0.0 |             0.0 |

    .. raw:: html

        <iframe
            src="dam_v004_ex10.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>

    :ref:`Exact recalculation of example 13 <dam_v003_ex13>`

    This example demonstrates the identical behaviour of models
    |dam_v003| and |dam_v004| (and also of models |dam_v001| and
    |dam_v002| regarding high flow conditions:

    >>> neardischargeminimumthreshold(0.0)
    >>> neardischargeminimumtolerance(0.0)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)
    >>> waterlevelminimumremotethreshold(0.0)
    >>> waterlevelminimumremotetolerance(0.0)
    >>> waterlevel2flooddischarge(ann(
    ...         weights_input=1e-6, weights_output=1e7,
    ...         intercepts_hidden=0.0, intercepts_output=-1e7/2))
    >>> neardischargeminimumthreshold(0.0)
    >>> inflow.sequences.sim.series = [ 0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...                                 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    >>> required_supply.sequences.sim.series = 0.0
    >>> test.inits.loggedrequiredremoterelease = 0.0
    >>> test('dam_v004_ex13')
    |   date | inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve | inflow |  release | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |            0.0 |      0.0 |         0.0 |            0.0 |           0.0 |             0.0 |    0.0 |      0.0 |             0.0 |
    | 02.01. |    1.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.026514 | 0.026514 |    0.084109 |            0.0 |           0.0 |             0.0 |    1.0 | 0.026514 |             0.0 |
    | 03.01. |    5.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.183744 | 0.183744 |    0.500234 |            0.0 |           0.0 |             0.0 |    5.0 | 0.183744 |             0.0 |
    | 04.01. |    9.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.542983 | 0.542983 |     1.23092 |            0.0 |           0.0 |             0.0 |    9.0 | 0.542983 |             0.0 |
    | 05.01. |    8.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.961039 | 0.961039 |    1.839086 |            0.0 |           0.0 |             0.0 |    8.0 | 0.961039 |             0.0 |
    | 06.01. |    5.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.251523 | 1.251523 |    2.162955 |            0.0 |           0.0 |             0.0 |    5.0 | 1.251523 |             0.0 |
    | 07.01. |    3.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.395546 | 1.395546 |    2.301579 |            0.0 |           0.0 |             0.0 |    3.0 | 1.395546 |             0.0 |
    | 08.01. |    2.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.453375 | 1.453375 |    2.348808 |            0.0 |           0.0 |             0.0 |    2.0 | 1.453375 |             0.0 |
    | 09.01. |    1.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.455596 | 1.455596 |    2.309444 |            0.0 |           0.0 |             0.0 |    1.0 | 1.455596 |             0.0 |
    | 10.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.405132 | 1.405132 |    2.188041 |            0.0 |           0.0 |             0.0 |    0.0 | 1.405132 |             0.0 |
    | 11.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.331267 | 1.331267 |    2.073019 |            0.0 |           0.0 |             0.0 |    0.0 | 1.331267 |             0.0 |
    | 12.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.261285 | 1.261285 |    1.964044 |            0.0 |           0.0 |             0.0 |    0.0 | 1.261285 |             0.0 |
    | 13.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.194981 | 1.194981 |    1.860798 |            0.0 |           0.0 |             0.0 |    0.0 | 1.194981 |             0.0 |
    | 14.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.132163 | 1.132163 |    1.762979 |            0.0 |           0.0 |             0.0 |    0.0 | 1.132163 |             0.0 |
    | 15.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.072647 | 1.072647 |    1.670302 |            0.0 |           0.0 |             0.0 |    0.0 | 1.072647 |             0.0 |
    | 16.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.01626 |  1.01626 |    1.582498 |            0.0 |           0.0 |             0.0 |    0.0 |  1.01626 |             0.0 |
    | 17.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.962837 | 0.962837 |    1.499308 |            0.0 |           0.0 |             0.0 |    0.0 | 0.962837 |             0.0 |
    | 18.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.912222 | 0.912222 |    1.420492 |            0.0 |           0.0 |             0.0 |    0.0 | 0.912222 |             0.0 |
    | 19.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.864268 | 0.864268 |     1.34582 |            0.0 |           0.0 |             0.0 |    0.0 | 0.864268 |             0.0 |
    | 20.01. |    0.0 |                   0.0 |                  0.0 |                   0.0 |                 0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.818835 | 0.818835 |    1.275072 |            0.0 |           0.0 |             0.0 |    0.0 | 0.818835 |             0.0 |

    .. raw:: html

        <iframe
            src="dam_v004_ex13.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>

    :ref:`Modification of example 13 <dam_v003_ex13>`

    Building on the example above, we demonstrate the possibility to
    constrain |ActualRemoteRelieve| and |ActualRemoteRelease| by setting
    parameter |HighestRemoteDischarge| to 1.0 m³/s, which is the allowed
    sum of both |AllowedRemoteRelieve| and |ActualRemoteRelease|:

    This final example demonstrates the identical behaviour of models
    |dam_v003| and |dam_v004| (and also of models |dam_v001| and
    |dam_v002| regarding high flow conditions:

    >>> test.inits.loggedrequiredremoterelease = 0.5
    >>> required_supply.sequences.sim.series = 0.5
    >>> test.inits.loggedallowedremoterelieve = 0.0
    >>> allowed_relieve.sequences.sim.series = numpy.linspace(0.0, 1.5, 20)
    >>> waterlevelminimumremotethreshold(0.0)
    >>> waterlevel2possibleremoterelieve(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=5.0)
    >>> highestremotedischarge(1.0)
    >>> highestremotetolerance(0.1)

    The following results demonstrate, that |AllowedRemoteRelieve|
    has priority over |ActualRemoteRelease|. |RequiredRemoteRelease| is
    set to a constant value of 0.5 m³/s via node `required_supply`,
    whereas |AllowedRemoteRelieve| increases linearly from 0.0 to 1.5 m³/s.
    Due to parameter |HighestRemoteDischarge| being set to 1.0 m³/s,
    |ActualRemoteRelease| starts to drop when |AllowedRemoteRelieve|
    exceeds 0.5 m³/s, and |AllowedRemoteRelieve| itself does
    never exceede 1 m³/s:

    >>> test('dam_v004_ex13_1')
    |   date | inflow | requiredremoterelease | allowedremoterelieve | possibleremoterelieve | actualremoterelieve | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | actual_relieve | actual_supply | allowed_relieve | inflow |  release | required_supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                   0.5 |                  0.0 |                   5.0 |                 0.0 |             0.0 |             0.0 |           0.0 |              0.0125 |      -0.001125 |      0.0 |    -0.00108 |            0.0 |        0.0125 |             0.0 |    0.0 |      0.0 |             0.5 |
    | 02.01. |    1.0 |                   0.5 |                  0.0 |                   5.0 |                 0.0 |             0.0 |             0.0 |           0.0 |            0.483321 |       0.013893 | 0.013915 |    0.042359 |            0.0 |      0.483321 |        0.078947 |    1.0 | 0.013915 |             0.5 |
    | 03.01. |    5.0 |                   0.5 |             0.078947 |                   5.0 |            0.078947 |             0.0 |             0.0 |           0.0 |            0.499952 |       0.142993 | 0.142993 |    0.411987 |       0.078947 |      0.499952 |        0.157895 |    5.0 | 0.142993 |             0.5 |
    | 04.01. |    9.0 |                   0.5 |             0.157895 |                   5.0 |            0.157895 |             0.0 |             0.0 |           0.0 |            0.499819 |       0.471852 | 0.471852 |    1.091993 |       0.157895 |      0.499819 |        0.236842 |    9.0 | 0.471852 |             0.5 |
    | 05.01. |    8.0 |                   0.5 |             0.236842 |                   5.0 |            0.236842 |             0.0 |             0.0 |           0.0 |            0.499314 |       0.856993 | 0.856993 |    1.645545 |       0.236842 |      0.499314 |        0.315789 |    8.0 | 0.856993 |             0.5 |
    | 06.01. |    5.0 |                   0.5 |             0.315789 |                   5.0 |            0.315789 |             0.0 |             0.0 |           0.0 |            0.497434 |       1.112205 | 1.112205 |    1.911188 |       0.315789 |      0.497434 |        0.394737 |    5.0 | 1.112205 |             0.5 |
    | 07.01. |    3.0 |                   0.5 |             0.394737 |                   5.0 |            0.394735 |             0.0 |             0.0 |           0.0 |            0.490789 |       1.218885 | 1.218885 |    1.988567 |       0.394735 |      0.490789 |        0.473684 |    3.0 | 1.218885 |             0.5 |
    | 08.01. |    2.0 |                   0.5 |             0.473684 |                   5.0 |            0.473676 |             0.0 |             0.0 |           0.0 |            0.470723 |       1.237798 | 1.237798 |    1.972825 |       0.473676 |      0.470723 |        0.552632 |    2.0 | 1.237798 |             0.5 |
    | 09.01. |    1.0 |                   0.5 |             0.552632 |                   5.0 |            0.552601 |             0.0 |             0.0 |           0.0 |            0.427028 |       1.200864 | 1.200864 |     1.87083 |       0.552601 |      0.427028 |        0.631579 |    1.0 | 1.200864 |             0.5 |
    | 10.01. |    0.0 |                   0.5 |             0.631579 |                   5.0 |            0.631463 |             0.0 |             0.0 |           0.0 |            0.362181 |       1.111921 | 1.111921 |     1.68891 |       0.631463 |      0.362181 |        0.710526 |    0.0 | 1.111921 |             0.5 |
    | 11.01. |    0.0 |                   0.5 |             0.710526 |                   5.0 |            0.710086 |             0.0 |             0.0 |           0.0 |            0.286864 |       1.001148 | 1.001148 |    1.516274 |       0.710086 |      0.286864 |        0.789474 |    0.0 | 1.001148 |             0.5 |
    | 12.01. |    0.0 |                   0.5 |             0.789474 |                   5.0 |            0.787817 |             0.0 |             0.0 |           0.0 |            0.208657 |       0.896124 | 0.896124 |    1.352753 |       0.787817 |      0.208657 |        0.868421 |    0.0 | 0.896124 |             0.5 |
    | 13.01. |    0.0 |                   0.5 |             0.868421 |                   5.0 |            0.862356 |             0.0 |             0.0 |           0.0 |            0.129881 |       0.796746 | 0.796746 |    1.198185 |       0.862356 |      0.129881 |        0.947368 |    0.0 | 0.796746 |             0.5 |
    | 14.01. |    0.0 |                   0.5 |             0.947368 |                   5.0 |            0.927029 |             0.0 |             0.0 |           0.0 |            0.051045 |       0.703078 | 0.703078 |    1.052934 |       0.927029 |      0.051045 |        1.026316 |    0.0 | 0.703078 |             0.5 |
    | 15.01. |    0.0 |                   0.5 |             1.026316 |                   5.0 |            0.970723 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.614897 | 0.614897 |    0.915936 |       0.970723 |           0.0 |        1.105263 |    0.0 | 0.614897 |             0.5 |
    | 16.01. |    0.0 |                   0.5 |             1.105263 |                   5.0 |            0.990741 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.531013 | 0.531013 |    0.784457 |       0.990741 |           0.0 |        1.184211 |    0.0 | 0.531013 |             0.5 |
    | 17.01. |    0.0 |                   0.5 |             1.184211 |                   5.0 |            0.996746 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.450858 | 0.450858 |    0.659384 |       0.996746 |           0.0 |        1.263158 |    0.0 | 0.450858 |             0.5 |
    | 18.01. |    0.0 |                   0.5 |             1.263158 |                   5.0 |            0.997993 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.374727 | 0.374727 |    0.540781 |       0.997993 |           0.0 |        1.342105 |    0.0 | 0.374727 |             0.5 |
    | 19.01. |    0.0 |                   0.5 |             1.342105 |                   5.0 |            0.998268 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.302558 | 0.302558 |    0.428389 |       0.998268 |           0.0 |        1.421053 |    0.0 | 0.302558 |             0.5 |
    | 20.01. |    0.0 |                   0.5 |             1.421053 |                   5.0 |            0.998337 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.234174 | 0.234174 |      0.3219 |       0.998337 |           0.0 |             1.5 |    0.0 | 0.234174 |             0.5 |

    .. raw:: html

        <iframe
            src="dam_v004_ex13_1.html"
            width="100%"
            height="330px"
            frameborder=0
        ></iframe>
"""

# import...
# ...from HydPy
from hydpy.auxs.anntools import ann   # pylint: disable=unused-import
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
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_RequiredRemoteRelease_V2,
        dam_model.Calc_AllowedRemoteRelieve_V1,
        dam_model.Calc_RequiredRelease_V2,
        dam_model.Calc_TargetedRelease_V1,
    )
    RECEIVER_METHODS = (
        dam_model.Pic_LoggedRequiredRemoteRelease_V2,
        dam_model.Pic_LoggedAllowedRemoteRelieve_V1,
    )
    PART_ODE_METHODS = (
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualRelease_V1,
        dam_model.Calc_PossibleRemoteRelieve_V1,
        dam_model.Calc_ActualRemoteRelieve_V1,
        dam_model.Calc_ActualRemoteRelease_V1,
        dam_model.Update_ActualRemoteRelease_V1,
        dam_model.Update_ActualRemoteRelieve_V1,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_Outflow_V1,
    )
    FULL_ODE_METHODS = (
        dam_model.Update_WaterVolume_V3,
    )
    OUTLET_METHODS = (
        dam_model.Pass_Outflow_V1,
        dam_model.Pass_ActualRemoteRelease_V1,
        dam_model.Pass_ActualRemoteRelieve_V1,
    )
    SENDER_METHODS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
