# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Version 4 of HydPy-Dam

    Application model |dam_v004| is an extension if model |dam_v003|.
    Both models are able to discharge water into the channel downstream
    and to remote locations.  The difference is that |dam_v003|
    can discharge water only to a single remote location, e.g. to a
    drinking water treatment plant, while |dam_v004| is also able to
    discharge water to a seperate remote location independently, e.g.
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

    >>> from hydpy import pub, Timegrid, Timegrids, Node, Element
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '21.01.2000',
    ...                                    '1d'))
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
    >>> dam.connect(model)

    The first test calculation is supposed to show that model |dam_v004|
    behaves exactly like model |dam_v003| when the relieve discharge is
    disabled, which can be accomplished by the following settings:

    >>> from hydpy.core.testtools import IntegrationTest
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
    >>> waterlevel2flooddischarge(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=0.0)
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
    >>> waterlevel2flooddischarge(
    ...         weights_input=1e-6, weights_output=1e7,
    ...         intercepts_hidden=0.0, intercepts_output=-1e7/2)
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

"""

# import...
# ...from standard library
from __future__ import division, print_function
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from HydPy
from hydpy.core.modelimports import *
# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_control
from hydpy.models.dam import dam_derived
from hydpy.models.dam import dam_solver
from hydpy.models.dam import dam_fluxes
from hydpy.models.dam import dam_states
from hydpy.models.dam import dam_logs
from hydpy.models.dam import dam_aides
from hydpy.models.dam import dam_inlets
from hydpy.models.dam import dam_outlets
from hydpy.models.dam import dam_receivers


class Model(modeltools.ModelELS):
    """Version 4 of HydPy-Dam."""

    _INLET_METHODS = (dam_model.pic_inflow_v1,
                      dam_model.calc_requiredremoterelease_v2,
                      dam_model.calc_allowedremoterelieve_v1,
                      dam_model.calc_requiredrelease_v2,
                      dam_model.calc_targetedrelease_v1)
    _RECEIVER_METHODS = (dam_model.pic_loggedrequiredremoterelease_v2,
                         dam_model.pic_loggedallowedremoterelieve_v1)
    _PART_ODE_METHODS = (dam_model.pic_inflow_v1,
                         dam_model.calc_waterlevel_v1,
                         dam_model.calc_actualrelease_v1,
                         dam_model.calc_possibleremoterelieve_v1,
                         dam_model.calc_actualremoterelieve_v1,
                         dam_model.calc_actualremoterelease_v1,
                         dam_model.calc_flooddischarge_v1,
                         dam_model.calc_outflow_v1)
    _FULL_ODE_METHODS = (dam_model.update_watervolume_v3,)
    _OUTLET_METHODS = (dam_model.pass_outflow_v1,
                       dam_model.pass_actualremoterelease_v1,
                       dam_model.pass_actualremoterelieve_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-Dam, Version 4."""
    _PARCLASSES = (dam_control.CatchmentArea,
                   dam_control.WaterLevel2PossibleRemoteRelieve,
                   dam_control.RemoteRelieveTolerance,
                   dam_control.NearDischargeMinimumThreshold,
                   dam_control.NearDischargeMinimumTolerance,
                   dam_control.WaterLevelMinimumThreshold,
                   dam_control.WaterLevelMinimumTolerance,
                   dam_control.WaterLevelMinimumRemoteThreshold,
                   dam_control.WaterLevelMinimumRemoteTolerance,
                   dam_control.WaterVolume2WaterLevel,
                   dam_control.WaterLevel2FloodDischarge)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-Dam, Version 4."""
    _PARCLASSES = (dam_derived.TOY,
                   dam_derived.Seconds,
                   dam_derived.NearDischargeMinimumSmoothPar1,
                   dam_derived.WaterLevelMinimumSmoothPar,
                   dam_derived.WaterLevelMinimumRemoteSmoothPar)


class SolverParameters(parametertools.SubParameters):
    """Solver parameters of HydPy-Dam, Version 4."""
    _PARCLASSES = (dam_solver.AbsErrorMax,
                   dam_solver.RelDTMin)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-Dam, Version 4."""
    _SEQCLASSES = (dam_fluxes.Inflow,
                   dam_fluxes.RequiredRemoteRelease,
                   dam_fluxes.AllowedRemoteRelieve,
                   dam_fluxes.PossibleRemoteRelieve,
                   dam_fluxes.ActualRemoteRelieve,
                   dam_fluxes.RequiredRelease,
                   dam_fluxes.TargetedRelease,
                   dam_fluxes.ActualRelease,
                   dam_fluxes.ActualRemoteRelease,
                   dam_fluxes.FloodDischarge,
                   dam_fluxes.Outflow)


class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-Dam, Version 4."""
    _SEQCLASSES = (dam_states.WaterVolume,)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of HydPy-Dam, Version 4."""
    _SEQCLASSES = (dam_logs.LoggedRequiredRemoteRelease,
                   dam_logs.LoggedAllowedRemoteRelieve)


class AideSequences(sequencetools.AideSequences):
    """State sequences of HydPy-Dam, Version 4."""
    _SEQCLASSES = (dam_aides.WaterLevel,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-Dam, Version 4."""
    _SEQCLASSES = (dam_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-Dam, Version 4."""
    _SEQCLASSES = (dam_outlets.Q,
                   dam_outlets.S,
                   dam_outlets.R)


class ReceiverSequences(sequencetools.LinkSequences):
    """Information link sequences of HydPy-Dam, Version 4."""
    _SEQCLASSES = (dam_receivers.S,
                   dam_receivers.R)


autodoc_applicationmodel()


# pylint: disable=invalid-name
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()