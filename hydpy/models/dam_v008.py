# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Reservoir version of HydPy-Dam.

.. _`LARSIM`: http://www.larsim.de/en/the-model/

|dam_v008| is a relatively simple reservoir model, similar to the "TALS"
model of `LARSIM`_.  It combines the features of |dam_v006| ("controlled
lake") and |dam_v007| ("retention basin").  Additionally, it allows
controlling the stored water volume via defining target values that can
vary seasonally.

Like |dam_v007|, |dam_v008| allows for combining controlled, "harmless
outflow" (via parameter |AllowedRelease|) and uncontrolled, "spillway
outflow" (via parameter |WaterLevel2FloodDischarge|), and like |dam_v006|,
it allows to restrict the speed of the water level decrease during periods
with little inflow via parameter |AllowedWaterLevelDrop| (only through
reducing the controlled outflow, of course).  Before continuing, please
first read the documentation on these two application models.

The additional feature of |dam_v008| is that it tries to track target
volumes that can vary seasonally.  Define these target volumes via
parameter |TargetVolume|.  The parameters |VolumeTolerance|,
|TargetRangeAbsolute|, and |TargetRangeRelative| serve to yield more
smooth and realistic reservoir responses for small deviations from
the given target values.  Setting |TargetRangeRelative| to 0.2 and
both other parameters to zero corresponds to selecting the
"TALSPERRE SOLLRANGE" option in `LARSIM`_.  Please see the following
examples and the documentation on method |Calc_ActualRelease_V3| for
more information on how to set and combine the individual parameter
values for different use-cases.

Integration tests
=================

.. how_to_understand_integration_tests::

We create the same test set as for application models |dam_v006| and
|dam_v007|, including an identical inflow series and an identical
relationship between stage and volume:

>>> from hydpy import IntegrationTest, Element, pub
>>> pub.timegrids = '01.01.2000', '21.01.2000', '1d'
>>> from hydpy.models.dam_v008 import *
>>> parameterstep('1d')
>>> element = Element('element', inlets='input_', outlets='output')
>>> element.model = model
>>> IntegrationTest.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> IntegrationTest.plotting_options.axis2 = states.watervolume
>>> test = IntegrationTest(element)
>>> test.inits = [(states.watervolume, 0.0)]
>>> test.dateformat = '%d.%m.'
>>> watervolume2waterlevel(
...     weights_input=1e-6, weights_output=4.e6,
...     intercepts_hidden=0.0, intercepts_output=-4e6/2)
>>> catchmentarea(86.4)
>>> element.inlets.input_.sequences.sim.series = [
...     0.0, 1.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

.. _dam_v008_base_scenario:

base scenario
_____________

First, we again use the quasi-linear relation between discharge
and stage used throughout the integration tests of |dam_v006| and in the
:ref:`dam_v006_base_scenario` example of |dam_v007|:

>>> waterlevel2flooddischarge(ann(
...     weights_input=1e-6, weights_output=4e7,
...     intercepts_hidden=0.0, intercepts_output=-4e7/2))

Additionally, we set some of the remaining parameter values extremely high
or low, to make sure that the reservoir stores all water except the one
activating the spillway and thus becoming "flood discharge":

>>> targetvolume(100.0)
>>> neardischargeminimumthreshold.shape = 1
>>> neardischargeminimumthreshold.values = -100.0
>>> targetrangeabsolute(0.1)
>>> targetrangerelative(0.2)
>>> volumetolerance(0.1)
>>> dischargetolerance(0.1)
>>> allowedrelease(100.0)
>>> allowedwaterleveldrop(100.0)

Due to the same the neural network configuration, the results are identical
with the ones of the :ref:`dam_v006_base_scenario` example of |dam_v006| and
the :ref:`dam_v007_base_scenario` example of |dam_v007|:

.. integration-test::

    >>> test('dam_v008_base_scenario')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |           0.0 |       0.329814 | 0.329814 |    0.057904 |    1.0 | 0.329814 |
    | 03.01. |    6.0 |           0.0 |       2.370574 | 2.370574 |    0.371486 |    6.0 | 2.370574 |
    | 04.01. |   12.0 |           0.0 |       6.452959 | 6.452959 |    0.850751 |   12.0 | 6.452959 |
    | 05.01. |   10.0 |           0.0 |       8.999753 | 8.999753 |    0.937172 |   10.0 | 8.999753 |
    | 06.01. |    6.0 |           0.0 |       8.257426 | 8.257426 |    0.742131 |    6.0 | 8.257426 |
    | 07.01. |    3.0 |           0.0 |        5.96014 |  5.96014 |    0.486374 |    3.0 |  5.96014 |
    | 08.01. |    2.0 |           0.0 |       3.917326 | 3.917326 |    0.320717 |    2.0 | 3.917326 |
    | 09.01. |    1.0 |           0.0 |       2.477741 | 2.477741 |    0.193041 |    1.0 | 2.477741 |
    | 10.01. |    0.0 |           0.0 |       1.293731 | 1.293731 |    0.081262 |    0.0 | 1.293731 |
    | 11.01. |    0.0 |           0.0 |       0.544608 | 0.544608 |    0.034208 |    0.0 | 0.544608 |
    | 12.01. |    0.0 |           0.0 |       0.227669 | 0.227669 |    0.014537 |    0.0 | 0.227669 |
    | 13.01. |    0.0 |           0.0 |       0.096753 | 0.096753 |    0.006178 |    0.0 | 0.096753 |
    | 14.01. |    0.0 |           0.0 |       0.042778 | 0.042778 |    0.002482 |    0.0 | 0.042778 |
    | 15.01. |    0.0 |           0.0 |       0.017186 | 0.017186 |    0.000997 |    0.0 | 0.017186 |
    | 16.01. |    0.0 |           0.0 |       0.005664 | 0.005664 |    0.000508 |    0.0 | 0.005664 |
    | 17.01. |    0.0 |           0.0 |       0.002884 | 0.002884 |    0.000259 |    0.0 | 0.002884 |
    | 18.01. |    0.0 |           0.0 |       0.001469 | 0.001469 |    0.000132 |    0.0 | 0.001469 |
    | 19.01. |    0.0 |           0.0 |       0.000748 | 0.000748 |    0.000067 |    0.0 | 0.000748 |
    | 20.01. |    0.0 |           0.0 |       0.000381 | 0.000381 |    0.000034 |    0.0 | 0.000381 |

.. _dam_v008_spillway:

spillway
________

When we reuse the more realistic relationship between flood discharge
and stage of the :ref:`dam_v007_spillway` example on |dam_v007|, we again
get the same flood discharge time series:

.. integration-test::

    >>> waterlevel2flooddischarge(ann(
    ...     weights_input=10.0, weights_output=50.0,
    ...     intercepts_hidden=-20.0, intercepts_output=0.0))
    >>> test('dam_v008_spillway')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |           0.0 |            0.0 |      0.0 |      0.0864 |    1.0 |      0.0 |
    | 03.01. |    6.0 |           0.0 |       0.000022 | 0.000022 |    0.604798 |    6.0 | 0.000022 |
    | 04.01. |   12.0 |           0.0 |       0.125869 | 0.125869 |    1.630723 |   12.0 | 0.125869 |
    | 05.01. |   10.0 |           0.0 |       7.337517 | 7.337517 |    1.860762 |   10.0 | 7.337517 |
    | 06.01. |    6.0 |           0.0 |       6.687413 | 6.687413 |    1.801369 |    6.0 | 6.687413 |
    | 07.01. |    3.0 |           0.0 |       3.829425 | 3.829425 |    1.729707 |    3.0 | 3.829425 |
    | 08.01. |    2.0 |           0.0 |       2.462161 | 2.462161 |    1.689776 |    2.0 | 2.462161 |
    | 09.01. |    1.0 |           0.0 |       1.602443 | 1.602443 |    1.637725 |    1.0 | 1.602443 |
    | 10.01. |    0.0 |           0.0 |       0.869271 | 0.869271 |     1.56262 |    0.0 | 0.869271 |
    | 11.01. |    0.0 |           0.0 |       0.498579 | 0.498579 |    1.519543 |    0.0 | 0.498579 |
    | 12.01. |    0.0 |           0.0 |       0.348504 | 0.348504 |    1.489432 |    0.0 | 0.348504 |
    | 13.01. |    0.0 |           0.0 |       0.267917 | 0.267917 |    1.466284 |    0.0 | 0.267917 |
    | 14.01. |    0.0 |           0.0 |       0.217618 | 0.217618 |    1.447482 |    0.0 | 0.217618 |
    | 15.01. |    0.0 |           0.0 |       0.183225 | 0.183225 |    1.431651 |    0.0 | 0.183225 |
    | 16.01. |    0.0 |           0.0 |       0.158219 | 0.158219 |    1.417981 |    0.0 | 0.158219 |
    | 17.01. |    0.0 |           0.0 |       0.139064 | 0.139064 |    1.405966 |    0.0 | 0.139064 |
    | 18.01. |    0.0 |           0.0 |       0.124197 | 0.124197 |    1.395235 |    0.0 | 0.124197 |
    | 19.01. |    0.0 |           0.0 |       0.112196 | 0.112196 |    1.385542 |    0.0 | 0.112196 |
    | 20.01. |    0.0 |           0.0 |       0.102307 | 0.102307 |    1.376702 |    0.0 | 0.102307 |

.. _dam_v008_target_volume:

target volume
_____________

During dry periods, application model |dam_v007| generally releases all
its water until the basin runs dry, as long as parameter |AllowedRelease|
is larger than zero.  Application model |dam_v008| is more complex, in that
it allows to define target storage volumes.  |dam_v008| tries to control
its outflow so that the actual volume approximately equals the (potentially
seasonally varying) target volume.  However, it cannot release arbitrary
low or high amounts of water to fulfil this task due to its priority to
release a predefined minimum amount of water (for ecological reasons) and
its second priority to not release to much water (for flood protection).
In this example, we activate these mechanisms through changing some related
parameter values (also see the documentation on method |Calc_ActualRelease_V3|
for more detailed examples, including the numerous corner cases):

>>> targetvolume(0.5)
>>> neardischargeminimumthreshold(0.1)
>>> allowedrelease(4.0)
>>> allowedwaterleveldrop(1.0)

Compared with the :ref:`dam_v007_allowed_release` results of |dam_v007|,
|dam_v008| dampens the given flood event less efficiently.  |dam_v007|
releases all initial inflow, while |dam_v008| stores most of it until
it reaches the target volume of 0.5 million m³.  After peak flow,
|dam_v008| first releases its water as fast as allowed, but then again
tries to meet the target volume.  The slow negative trend away from the
target value at the end of the simulation period results from the lack
of inflow while there is still the necessity to release at least 0.1 m³/s:

.. integration-test::

    >>> test('dam_v008_target_volume')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |      0.052009 |            0.0 |  0.05201 |   -0.004494 |    0.0 |  0.05201 |
    | 02.01. |    1.0 |      0.087534 |            0.0 | 0.087534 |    0.074343 |    1.0 | 0.087534 |
    | 03.01. |    6.0 |      1.053864 |       0.000005 | 1.053869 |    0.501689 |    6.0 | 1.053869 |
    | 04.01. |   12.0 |      3.999813 |       0.007819 | 4.007632 |     1.19223 |   12.0 | 4.007632 |
    | 05.01. |   10.0 |           4.0 |       0.430009 | 4.430009 |    1.673477 |   10.0 | 4.430009 |
    | 06.01. |    6.0 |           4.0 |       1.919462 | 5.919462 |    1.680435 |    6.0 | 5.919462 |
    | 07.01. |    3.0 |           4.0 |       0.892331 | 4.892331 |    1.516938 |    3.0 | 4.892331 |
    | 08.01. |    2.0 |           4.0 |       0.174933 | 4.174933 |    1.329024 |    2.0 | 4.174933 |
    | 09.01. |    1.0 |           4.0 |       0.021533 | 4.021533 |    1.067963 |    1.0 | 4.021533 |
    | 10.01. |    0.0 |      3.999928 |        0.00231 | 4.002237 |     0.72217 |    0.0 | 4.002237 |
    | 11.01. |    0.0 |      2.363579 |       0.000045 | 2.363624 |    0.517953 |    0.0 | 2.363624 |
    | 12.01. |    0.0 |      0.171571 |       0.000017 | 0.171588 |    0.503128 |    0.0 | 0.171588 |
    | 13.01. |    0.0 |      0.120742 |       0.000015 | 0.120757 |    0.492694 |    0.0 | 0.120757 |
    | 14.01. |    0.0 |      0.120116 |       0.000014 |  0.12013 |    0.482315 |    0.0 |  0.12013 |
    | 15.01. |    0.0 |      0.118399 |       0.000012 | 0.118411 |    0.472084 |    0.0 | 0.118411 |
    | 16.01. |    0.0 |      0.116632 |       0.000011 | 0.116643 |    0.462006 |    0.0 | 0.116643 |
    | 17.01. |    0.0 |        0.1154 |        0.00001 |  0.11541 |    0.452035 |    0.0 |  0.11541 |
    | 18.01. |    0.0 |      0.114385 |       0.000009 | 0.114394 |    0.442151 |    0.0 | 0.114394 |
    | 19.01. |    0.0 |      0.113448 |       0.000008 | 0.113456 |    0.432349 |    0.0 | 0.113456 |
    | 20.01. |    0.0 |      0.112549 |       0.000007 | 0.112556 |    0.422624 |    0.0 | 0.112556 |

.. _dam_v008_sharp_transitions:

sharp transitions
_________________

Due to smoothing, the above results deviate from the ones one would
expect from `LARSIM`_ simulations to some degree.  However, if we set both
"target range" parameters to zero (like one does not set the `LARSIM`_ option
"TALSPERRE SOLLRANGE") and both "tolerance" parameters to zero (to
disable any smoothing), we should get more similar results:

.. integration-test::

    >>> targetrangeabsolute(0.0)
    >>> targetrangerelative(0.0)
    >>> volumetolerance(0.0)
    >>> dischargetolerance(0.0)
    >>> test('dam_v008_sharp_transitions')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |      0.004167 |            0.0 | 0.004167 |    -0.00036 |    0.0 | 0.004167 |
    | 02.01. |    1.0 |      0.091667 |            0.0 | 0.091667 |     0.07812 |    1.0 | 0.091667 |
    | 03.01. |    6.0 |       0.76924 |       0.000007 | 0.769247 |    0.530057 |    6.0 | 0.769247 |
    | 04.01. |   12.0 |           4.0 |       0.003864 | 4.003864 |    1.220923 |   12.0 | 4.003864 |
    | 05.01. |   10.0 |           4.0 |       0.541413 | 4.541413 |    1.692545 |   10.0 | 4.541413 |
    | 06.01. |    6.0 |           4.0 |       2.097129 | 6.097129 |    1.684153 |    6.0 | 6.097129 |
    | 07.01. |    3.0 |           4.0 |       0.915365 | 4.915365 |    1.518666 |    3.0 | 4.915365 |
    | 08.01. |    2.0 |           4.0 |       0.177742 | 4.177742 |    1.330509 |    2.0 | 4.177742 |
    | 09.01. |    1.0 |           4.0 |       0.021852 | 4.021852 |    1.069421 |    1.0 | 4.021852 |
    | 10.01. |    0.0 |           4.0 |       0.002344 | 4.002344 |    0.723618 |    0.0 | 4.002344 |
    | 11.01. |    0.0 |      2.627574 |       0.000043 | 2.627618 |    0.496592 |    0.0 | 2.627618 |
    | 12.01. |    0.0 |           0.1 |       0.000014 | 0.100014 |    0.487951 |    0.0 | 0.100014 |
    | 13.01. |    0.0 |           0.1 |       0.000013 | 0.100013 |     0.47931 |    0.0 | 0.100013 |
    | 14.01. |    0.0 |           0.1 |       0.000012 | 0.100012 |    0.470669 |    0.0 | 0.100012 |
    | 15.01. |    0.0 |           0.1 |       0.000011 | 0.100011 |    0.462028 |    0.0 | 0.100011 |
    | 16.01. |    0.0 |           0.1 |        0.00001 |  0.10001 |    0.453387 |    0.0 |  0.10001 |
    | 17.01. |    0.0 |           0.1 |       0.000009 | 0.100009 |    0.444746 |    0.0 | 0.100009 |
    | 18.01. |    0.0 |           0.1 |       0.000008 | 0.100008 |    0.436105 |    0.0 | 0.100008 |
    | 19.01. |    0.0 |           0.1 |       0.000008 | 0.100008 |    0.427465 |    0.0 | 0.100008 |
    | 20.01. |    0.0 |           0.1 |       0.000007 | 0.100007 |    0.418824 |    0.0 | 0.100007 |

.. _dam_v008_higher_accuracy:

higher accuracy
_______________

The first water volume calculated in the :ref:`dam_v008_sharp_transitions`
example is negative, which is the result of the limited numerical accuracy of
the underlying integration algorithm.  We can decrease such errors through
defining smaller error tolerance values, but at the risk of relevant
increases in computation times (especially in case one does apply zero
smoothing values):

.. integration-test::

    >>> solver.abserrormax(1e-6)
    >>> test('dam_v008_higher_accuracy')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |      0.000002 |            0.0 | 0.000002 |         0.0 |    0.0 | 0.000002 |
    | 02.01. |    1.0 |      0.099998 |            0.0 | 0.099998 |     0.07776 |    1.0 | 0.099998 |
    | 03.01. |    6.0 |      0.769489 |       0.000006 | 0.769495 |    0.529676 |    6.0 | 0.769495 |
    | 04.01. |   12.0 |           4.0 |       0.002983 | 4.002983 |    1.220618 |   12.0 | 4.002983 |
    | 05.01. |   10.0 |           4.0 |       0.539399 | 4.539399 |    1.692414 |   10.0 | 4.539399 |
    | 06.01. |    6.0 |           4.0 |       2.096604 | 6.096604 |    1.684067 |    6.0 | 6.096604 |
    | 07.01. |    3.0 |           4.0 |       0.914146 | 4.914146 |    1.518685 |    3.0 | 4.914146 |
    | 08.01. |    2.0 |           4.0 |       0.177989 | 4.177989 |    1.330507 |    2.0 | 4.177989 |
    | 09.01. |    1.0 |           4.0 |       0.021856 | 4.021856 |    1.069419 |    1.0 | 4.021856 |
    | 10.01. |    0.0 |           4.0 |       0.001273 | 4.001273 |    0.723709 |    0.0 | 4.001273 |
    | 11.01. |    0.0 |      2.626076 |       0.000042 | 2.626118 |    0.496812 |    0.0 | 2.626118 |
    | 12.01. |    0.0 |           0.1 |       0.000014 | 0.100014 |    0.488171 |    0.0 | 0.100014 |
    | 13.01. |    0.0 |           0.1 |       0.000013 | 0.100013 |     0.47953 |    0.0 | 0.100013 |
    | 14.01. |    0.0 |           0.1 |       0.000012 | 0.100012 |    0.470889 |    0.0 | 0.100012 |
    | 15.01. |    0.0 |           0.1 |       0.000011 | 0.100011 |    0.462248 |    0.0 | 0.100011 |
    | 16.01. |    0.0 |           0.1 |        0.00001 |  0.10001 |    0.453607 |    0.0 |  0.10001 |
    | 17.01. |    0.0 |           0.1 |       0.000009 | 0.100009 |    0.444966 |    0.0 | 0.100009 |
    | 18.01. |    0.0 |           0.1 |       0.000008 | 0.100008 |    0.436325 |    0.0 | 0.100008 |
    | 19.01. |    0.0 |           0.1 |       0.000008 | 0.100008 |    0.427685 |    0.0 | 0.100008 |
    | 20.01. |    0.0 |           0.1 |       0.000007 | 0.100007 |    0.419044 |    0.0 | 0.100007 |

.. _dam_v008_target_range:

target range
____________

In the last example, the behaviour of the reservoir always changes abruptly
when the actual volume transcends the target volume. According to its
documentation, `LARSIM`_ then predicts unrealistic jumps in discharge.
To solve this issue, `LARSIM`_ offers the "TALSPERRE SOLLRANGE" option,
which ensures smoother transitions between 80 % and 120 % of the target
volume, accomplished by linear interpolation.  |dam_v008| should never
output similar jumps as it controls the correctness of its results.
As a drawback, correcting these jumps (which still occur "unseeable" and
possibly multiple times within each affected simulation time step) costs
computation time.  Hence, at least when using small smoothing parameter
values, |dam_v008| can also benefit from this approach.  You can define
the range of interpolation freely via parameters |TargetRangeAbsolute| and
|TargetRangeRelative| depending on your specific needs.  Setting the latter
to 0.2 corresponds to the original "TALSPERRE SOLLRANGE"-configuration:

.. integration-test::

    >>> targetrangerelative(0.2)
    >>> test('dam_v008_target_range')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |      0.000002 |            0.0 | 0.000002 |         0.0 |    0.0 | 0.000002 |
    | 02.01. |    1.0 |      0.099998 |            0.0 | 0.099998 |     0.07776 |    1.0 | 0.099998 |
    | 03.01. |    6.0 |       1.01934 |       0.000005 | 1.019345 |    0.508089 |    6.0 | 1.019345 |
    | 04.01. |   12.0 |           4.0 |       0.002404 | 4.002404 |    1.199081 |   12.0 | 4.002404 |
    | 05.01. |   10.0 |           4.0 |       0.454147 | 4.454147 |    1.678243 |   10.0 | 4.454147 |
    | 06.01. |    6.0 |           4.0 |       1.963095 | 5.963095 |    1.681431 |    6.0 | 5.963095 |
    | 07.01. |    3.0 |           4.0 |       0.897827 | 4.897827 |    1.517459 |    3.0 | 4.897827 |
    | 08.01. |    2.0 |           4.0 |       0.175985 | 4.175985 |    1.329454 |    2.0 | 4.175985 |
    | 09.01. |    1.0 |           4.0 |       0.021629 | 4.021629 |    1.068385 |    1.0 | 4.021629 |
    | 10.01. |    0.0 |           4.0 |        0.00126 |  4.00126 |    0.722676 |    0.0 |  4.00126 |
    | 11.01. |    0.0 |      2.471849 |       0.000044 | 2.471893 |    0.509105 |    0.0 | 2.471893 |
    | 12.01. |    0.0 |      0.160404 |       0.000015 |  0.16042 |    0.495244 |    0.0 |  0.16042 |
    | 13.01. |    0.0 |           0.1 |       0.000014 | 0.100014 |    0.486603 |    0.0 | 0.100014 |
    | 14.01. |    0.0 |           0.1 |       0.000013 | 0.100013 |    0.477962 |    0.0 | 0.100013 |
    | 15.01. |    0.0 |           0.1 |       0.000012 | 0.100012 |    0.469321 |    0.0 | 0.100012 |
    | 16.01. |    0.0 |           0.1 |       0.000011 | 0.100011 |     0.46068 |    0.0 | 0.100011 |
    | 17.01. |    0.0 |           0.1 |        0.00001 |  0.10001 |    0.452039 |    0.0 |  0.10001 |
    | 18.01. |    0.0 |           0.1 |       0.000009 | 0.100009 |    0.443399 |    0.0 | 0.100009 |
    | 19.01. |    0.0 |           0.1 |       0.000008 | 0.100008 |    0.434758 |    0.0 | 0.100008 |
    | 20.01. |    0.0 |           0.1 |       0.000008 | 0.100008 |    0.426117 |    0.0 | 0.100008 |
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
    """Version 8 of HydPy-Dam."""
    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        dam_model.Pic_Inflow_V1,
    )
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_SurfaceArea_V1,
        dam_model.Calc_AllowedDischarge_V2,
        dam_model.Calc_ActualRelease_V3,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_Outflow_V1,
    )
    FULL_ODE_METHODS = (
        dam_model.Update_WaterVolume_V1,
    )
    OUTLET_METHODS = (
        dam_model.Pass_Outflow_V1,
    )
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
