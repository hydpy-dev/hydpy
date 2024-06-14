# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""
The *HydPy-SW1D* model family member |sw1d_network| allows combining different
storage and routing submodels for representing the 1-dimensional flow processes within
a complete channel network.

Technically, |sw1d_network| is quite similar to |sw1d_channel|, but both serve
different purposes and complement each other.  |sw1d_network| is a "composite model",
of which *HydPy* automatically creates instances, each of them combining the
submodels of multiple |sw1d_channel| instances.  So, framework users do usually not
need to configure |sw1d_network| directly but do so indirectly by preparing seemingly
independent |sw1d_channel| models for the individual reaches of a channel network.
Nevertheless, reading the following notes (after reading the |sw1d_channel|
documentation) might give some relevant insights as |sw1d_network| actually does the
simulation job and makes some demands regarding the "completeness" of the underlying
|sw1d_channel| models.

Integration tests
=================

.. how_to_understand_integration_tests::

The following examples build on the ones of the |sw1d_channel| documentation.  So, we
select the same simulation period:

>>> from hydpy import pub
>>> pub.timegrids = "2000-01-01 00:00", "2000-01-01 05:00", "5m"

We split the 20 km channel from the |sw1d_channel| documentation into two identical
parts.

We take the 20 km channel from the |sw1d_channel| documentation but split it into two
identical parts.  So, one |sw1d_channel| model, handled by the |Element| `channel1a`,
covers the first four segments and another one, handled by the |Element| `channel2`,
covers the last four segments.  But first, we need to define three nodes that are
connectable to the inlet sequence |sw1d_inlets.LongQ| and outlet sequence
|sw1d_outlets.LongQ|, which is simplest by defining their variable via a string:

>>> from hydpy import Node
>>> q_1a_in = Node("q_1a_in", variable="LongQ")
>>> q_1to2 = Node("q_1to2", variable="LongQ")
>>> q_2_out = Node("q_2_out", variable="LongQ")

The remarkable thing about defining the two elements is that we must associate them
with the same |Element.collective| so that *HydPy* knows it must combine their "user
models" into one "composite model":

>>> from hydpy import Element
>>> channel1a = Element("channel1a", collective="network", inlets=q_1a_in, outlets=q_1to2)
>>> channel2 = Element("channel2", collective="network", inlets=q_1to2, outlets=q_2_out)

Now, we set up all submodels as in the |sw1d_channel| documentation but assign each to
one of two main models, which in turn are handled by the two already available
elements:

>>> from hydpy import prepare_model
>>> from hydpy.models import sw1d_channel, sw1d_storage, sw1d_lias
>>> lengths = 2.0, 3.0, 2.0, 3.0
>>> for element in (channel1a, channel2):
...     channel = prepare_model(sw1d_channel)
...     channel.parameters.control.nmbsegments(4)
...     for i, length_ in enumerate(lengths):
...         with channel.add_storagemodel_v1(sw1d_storage, position=i):
...             length(length_)
...             with model.add_crosssection_v2("wq_trapeze"):
...                 nmbtrapezes(1)
...                 bottomlevels(5.0)
...                 bottomwidths(5.0)
...                 sideslopes(0.0)
...     for i in range(1, 5 if element is channel1a else 4):
...         with channel.add_routingmodel_v2(sw1d_lias, position=i):
...             lengthupstream(2.0 if i % 2 else 3.0)
...             lengthdownstream(3.0 if i % 2 else 2.0)
...             stricklercoefficient(1.0/0.03)
...             timestepfactor(0.7)
...             diffusionfactor(0.2)
...             with model.add_crosssection_v2("wq_trapeze"):
...                 nmbtrapezes(1)
...                 bottomlevels(5.0)
...                 bottomwidths(5.0)
...                 sideslopes(0.0)
...     element.model = channel

The following test function object finds all nodes and elements automatically upon
initialisation:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest()

We again define a convenience function for preparing the initial conditions.  This one
accepts individual water depths for different elements but generally sets the "old"
discharge to zero:

>>> def prepare_inits(**name2depth):
...     inits = []
...     for name, h in name2depth.items():
...         e = Element(name)
...         for s in e.model.storagemodels:
...             length = s.parameters.control.length
...             c = s.crosssection.parameters.control
...             v = h * (c.bottomwidths[0] + h * c.sideslopes[0]) * length
...             inits.append((s.sequences.states.watervolume, v))
...         for r in e.model.routingmodels:
...             if r is not None:
...                 inits.append((r.sequences.states.discharge, 0.0))
...     test.inits = inits


.. _sw1d_network_zero_inflow_and_outflow:

Zero inflow and outflow
_______________________

The following water depths agree with the configuration of the
:ref:`sw1d_channel_zero_inflow_and_outflow` example of |sw1d_channel|:

>>> prepare_inits(channel1a=3.0, channel2=1.0)

Albeit irrelevant for the first simulation, we set the inflow represented by the (still
unused) node `q_1a_in` to zero to avoid `nan` values in the following result table:

>>> q_1a_in.sequences.sim.series = 0.0

The discharge simulated for node `q_1to2` is identical to the one simulated for the
middle position in the :ref:`sw1d_channel_zero_inflow_and_outflow` example of
|sw1d_channel|, which shows that the |sw1d_network| instance here works as a correct
composite of the two user models:

.. integration-test::

    >>> conditions = test(get_conditions="2000-01-01 00:00")
    |                date |  timestep | q_1a_in |    q_1to2 | q_2_out |
    -------------------------------------------------------------------
    | 2000-01-01 00:00:00 | 41.932744 |     0.0 | 17.116697 |     0.0 |
    | 2000-01-01 00:05:00 | 41.932744 |     0.0 |  6.434402 |     0.0 |
    | 2000-01-01 00:10:00 |  41.86989 |     0.0 |  7.317577 |     0.0 |
    | 2000-01-01 00:15:00 | 40.570615 |     0.0 |  6.771817 |     0.0 |
    | 2000-01-01 00:20:00 | 38.464288 |     0.0 |  6.441228 |     0.0 |
    | 2000-01-01 00:25:00 | 36.060713 |     0.0 |  6.111343 |     0.0 |
    | 2000-01-01 00:30:00 | 33.726739 |     0.0 |  5.814913 |     0.0 |
    | 2000-01-01 00:35:00 | 31.578426 |     0.0 |  5.548742 |     0.0 |
    | 2000-01-01 00:40:00 | 29.590331 |     0.0 |  5.307354 |     0.0 |
    | 2000-01-01 00:45:00 | 27.697934 |     0.0 |  5.084325 |     0.0 |
    | 2000-01-01 00:50:00 | 25.854608 |     0.0 |  4.875904 |     0.0 |
    | 2000-01-01 00:55:00 | 24.044617 |     0.0 |  4.680467 |     0.0 |
    | 2000-01-01 01:00:00 | 22.271186 |     0.0 |  4.497034 |     0.0 |
    | 2000-01-01 01:05:00 | 20.541621 |     0.0 |  4.324343 |     0.0 |
    | 2000-01-01 01:10:00 | 18.859766 |     0.0 |  4.160846 |     0.0 |
    | 2000-01-01 01:15:00 | 17.225223 |     0.0 |   4.00511 |     0.0 |
    | 2000-01-01 01:20:00 | 15.635338 |     0.0 |  3.856098 |     0.0 |
    | 2000-01-01 01:25:00 | 14.087165 |     0.0 |  3.713189 |     0.0 |
    | 2000-01-01 01:30:00 | 12.578396 |     0.0 |  3.576035 |     0.0 |
    | 2000-01-01 01:35:00 | 11.107466 |     0.0 |  3.444403 |     0.0 |
    | 2000-01-01 01:40:00 |   9.67329 |     0.0 |  3.318058 |     0.0 |
    | 2000-01-01 01:45:00 |  8.274999 |     0.0 |  3.196719 |     0.0 |
    | 2000-01-01 01:50:00 |   6.91179 |     0.0 |  3.080056 |     0.0 |
    | 2000-01-01 01:55:00 |  5.582889 |     0.0 |  2.967695 |     0.0 |
    | 2000-01-01 02:00:00 |  4.287568 |     0.0 |  2.859236 |     0.0 |
    | 2000-01-01 02:05:00 |  3.025166 |     0.0 |  2.754256 |     0.0 |
    | 2000-01-01 02:10:00 |  1.795106 |     0.0 |  2.652318 |     0.0 |
    | 2000-01-01 02:15:00 |  0.596896 |     0.0 |  2.552973 |     0.0 |
    | 2000-01-01 02:20:00 |     300.0 |     0.0 |  2.455693 |     0.0 |
    | 2000-01-01 02:25:00 |     300.0 |     0.0 |  2.370851 |     0.0 |
    | 2000-01-01 02:30:00 |     300.0 |     0.0 |  2.278535 |     0.0 |
    | 2000-01-01 02:35:00 |     300.0 |     0.0 |  2.186283 |     0.0 |
    | 2000-01-01 02:40:00 |     300.0 |     0.0 |  2.094209 |     0.0 |
    | 2000-01-01 02:45:00 |     300.0 |     0.0 |  2.001626 |     0.0 |
    | 2000-01-01 02:50:00 |     300.0 |     0.0 |  1.908479 |     0.0 |
    | 2000-01-01 02:55:00 |     300.0 |     0.0 |  1.814849 |     0.0 |
    | 2000-01-01 03:00:00 |     300.0 |     0.0 |  1.720515 |     0.0 |
    | 2000-01-01 03:05:00 |     300.0 |     0.0 |  1.625017 |     0.0 |
    | 2000-01-01 03:10:00 |     300.0 |     0.0 |  1.527933 |     0.0 |
    | 2000-01-01 03:15:00 |     300.0 |     0.0 |  1.429057 |     0.0 |
    | 2000-01-01 03:20:00 |     300.0 |     0.0 |  1.328408 |     0.0 |
    | 2000-01-01 03:25:00 |     300.0 |     0.0 |   1.22614 |     0.0 |
    | 2000-01-01 03:30:00 |     300.0 |     0.0 |  1.122462 |     0.0 |
    | 2000-01-01 03:35:00 |     300.0 |     0.0 |  1.017589 |     0.0 |
    | 2000-01-01 03:40:00 |     300.0 |     0.0 |  0.911751 |     0.0 |
    | 2000-01-01 03:45:00 |     300.0 |     0.0 |  0.805203 |     0.0 |
    | 2000-01-01 03:50:00 |     300.0 |     0.0 |  0.698243 |     0.0 |
    | 2000-01-01 03:55:00 |     300.0 |     0.0 |  0.591202 |     0.0 |
    | 2000-01-01 04:00:00 |     300.0 |     0.0 |  0.484427 |     0.0 |
    | 2000-01-01 04:05:00 |     300.0 |     0.0 |  0.378258 |     0.0 |
    | 2000-01-01 04:10:00 |     300.0 |     0.0 |  0.273014 |     0.0 |
    | 2000-01-01 04:15:00 |     300.0 |     0.0 |   0.16898 |     0.0 |
    | 2000-01-01 04:20:00 |     300.0 |     0.0 |  0.066424 |     0.0 |
    | 2000-01-01 04:25:00 |     300.0 |     0.0 | -0.034386 |     0.0 |
    | 2000-01-01 04:30:00 |     300.0 |     0.0 | -0.131043 |     0.0 |
    | 2000-01-01 04:35:00 |     300.0 |     0.0 | -0.214119 |     0.0 |
    | 2000-01-01 04:40:00 |     300.0 |     0.0 | -0.278681 |     0.0 |
    | 2000-01-01 04:45:00 |     300.0 |     0.0 | -0.323311 |     0.0 |
    | 2000-01-01 04:50:00 |     300.0 |     0.0 | -0.349079 |     0.0 |
    | 2000-01-01 04:55:00 |     300.0 |     0.0 | -0.358235 |     0.0 |

There is no indication of an error in the water balance:

>>> from hydpy import round_
>>> round_(test.hydpy.collectives[0].model.check_waterbalance(conditions))
0.0

.. _sw1d_network_weir_outflow:

Weir outflow
____________

Next, we repeat the :ref:`sw1d_channel_weir_outflow` example of |sw1d_channel| as a
more complex example considering inflow and outflow.

We add an identical |sw1d_q_in| submodel at the inflow position of the upper element's
model:

>>> from hydpy.models import sw1d_q_in
>>> with channel1a.model.add_routingmodel_v1(sw1d_q_in, position=0):
...     lengthdownstream(2.0)
...     timestepfactor(0.7)
...     with model.add_crosssection_v2("wq_trapeze"):
...         nmbtrapezes(1)
...         bottomlevels(5.0)
...         bottomwidths(5.0)
...         sideslopes(0.0)
>>> channel1a.model.connect()

And we add an identical |sw1d_weir_out| submodel at the outflow position of the lower
element's model:

>>> from hydpy.models import sw1d_weir_out
>>> with channel2.model.add_routingmodel_v3(sw1d_weir_out, position=4):
...     lengthupstream(3.0)
...     crestheight(7.0)
...     crestwidth(5.0)
...     flowcoefficient(0.58)
...     timestepfactor(0.7)
>>> channel2.model.connect()

Further, we set the time step factor, the constant inflow, and the initial conditions to
the same values as in the :ref:`sw1d_channel_weir_outflow` example:

>>> test = IntegrationTest()
>>> for element in (channel1a, channel2):
...     for routingmodel in element.model.routingmodels.submodels:
...         if routingmodel is not None:
...             routingmodel.parameters.control.timestepfactor(0.1)
>>> q_1a_in.sequences.sim.series = 1.0
>>> prepare_inits(channel1a=2.0, channel2=2.0)

The following discharges are identical to those available in the results table of the
:ref:`sw1d_channel_weir_outflow` example of |sw1d_channel|:

.. integration-test::

    >>> conditions = test(get_conditions="2000-01-01 00:00")
    |                date |  timestep | q_1a_in |   q_1to2 |  q_2_out |
    -------------------------------------------------------------------
    | 2000-01-01 00:00:00 | 29.522473 |     1.0 | 0.000084 |      0.0 |
    | 2000-01-01 00:05:00 | 30.437257 |     1.0 | 0.010297 |      0.0 |
    | 2000-01-01 00:10:00 | 31.047327 |     1.0 | 0.057861 |      0.0 |
    | 2000-01-01 00:15:00 | 31.487924 |     1.0 |  0.13627 | 0.000003 |
    | 2000-01-01 00:20:00 | 31.831217 |     1.0 | 0.223131 | 0.000031 |
    | 2000-01-01 00:25:00 | 32.115718 |     1.0 | 0.303889 | 0.000173 |
    | 2000-01-01 00:30:00 | 32.362765 |     1.0 | 0.372712 | 0.000611 |
    | 2000-01-01 00:35:00 | 32.584688 |     1.0 | 0.428534 | 0.001597 |
    | 2000-01-01 00:40:00 | 32.788919 |     1.0 | 0.472255 | 0.003371 |
    | 2000-01-01 00:45:00 | 32.980171 |     1.0 | 0.505411 | 0.006095 |
    | 2000-01-01 00:50:00 | 33.161638 |     1.0 |  0.52966 | 0.009817 |
    | 2000-01-01 00:55:00 | 33.335665 |     1.0 | 0.546602 | 0.014488 |
    | 2000-01-01 01:00:00 |   33.5041 |     1.0 | 0.557716 | 0.019988 |
    | 2000-01-01 01:05:00 | 33.668478 |     1.0 | 0.564322 |  0.02617 |
    | 2000-01-01 01:10:00 | 33.830091 |     1.0 | 0.567571 | 0.032882 |
    | 2000-01-01 01:15:00 | 33.990019 |     1.0 | 0.568434 | 0.039987 |
    | 2000-01-01 01:20:00 | 34.149135 |     1.0 | 0.567713 | 0.047372 |
    | 2000-01-01 01:25:00 | 34.308116 |     1.0 | 0.566046 | 0.054949 |
    | 2000-01-01 01:30:00 | 34.467448 |     1.0 | 0.563931 | 0.062652 |
    | 2000-01-01 01:35:00 | 34.627446 |     1.0 |  0.56174 | 0.070436 |
    | 2000-01-01 01:40:00 | 34.788273 |     1.0 | 0.559739 | 0.078272 |
    | 2000-01-01 01:45:00 | 34.949971 |     1.0 |  0.55811 | 0.086141 |
    | 2000-01-01 01:50:00 | 35.112477 |     1.0 | 0.556964 | 0.094032 |
    | 2000-01-01 01:55:00 | 35.275657 |     1.0 | 0.556359 | 0.101942 |
    | 2000-01-01 02:00:00 | 35.439325 |     1.0 | 0.556315 | 0.109869 |
    | 2000-01-01 02:05:00 | 35.603263 |     1.0 | 0.556821 | 0.117813 |
    | 2000-01-01 02:10:00 | 35.767241 |     1.0 | 0.557846 | 0.125776 |
    | 2000-01-01 02:15:00 | 35.931023 |     1.0 | 0.559348 | 0.133758 |
    | 2000-01-01 02:20:00 | 36.094387 |     1.0 | 0.561277 | 0.141761 |
    | 2000-01-01 02:25:00 | 36.257123 |     1.0 | 0.563583 | 0.149785 |
    | 2000-01-01 02:30:00 | 36.419042 |     1.0 | 0.566213 |  0.15783 |
    | 2000-01-01 02:35:00 | 36.579976 |     1.0 | 0.569119 | 0.165895 |
    | 2000-01-01 02:40:00 | 36.739783 |     1.0 | 0.572257 |  0.17398 |
    | 2000-01-01 02:45:00 |  36.89834 |     1.0 | 0.575586 | 0.182081 |
    | 2000-01-01 02:50:00 | 37.055547 |     1.0 |  0.57907 | 0.190197 |
    | 2000-01-01 02:55:00 |  37.21132 |     1.0 | 0.582678 | 0.198324 |
    | 2000-01-01 03:00:00 | 37.365596 |     1.0 | 0.586386 |  0.20646 |
    | 2000-01-01 03:05:00 | 37.518323 |     1.0 | 0.590169 |   0.2146 |
    | 2000-01-01 03:10:00 | 37.669464 |     1.0 | 0.594011 | 0.222742 |
    | 2000-01-01 03:15:00 |  37.81899 |     1.0 | 0.597895 | 0.230882 |
    | 2000-01-01 03:20:00 | 37.966882 |     1.0 |  0.60181 | 0.239015 |
    | 2000-01-01 03:25:00 | 38.113129 |     1.0 | 0.605746 | 0.247138 |
    | 2000-01-01 03:30:00 | 38.257724 |     1.0 | 0.609694 | 0.255248 |
    | 2000-01-01 03:35:00 | 38.400665 |     1.0 | 0.613648 | 0.263341 |
    | 2000-01-01 03:40:00 | 38.541953 |     1.0 | 0.617604 | 0.271413 |
    | 2000-01-01 03:45:00 | 38.681592 |     1.0 | 0.621557 | 0.279461 |
    | 2000-01-01 03:50:00 |  38.81959 |     1.0 | 0.625503 | 0.287482 |
    | 2000-01-01 03:55:00 | 38.955953 |     1.0 | 0.629441 | 0.295473 |
    | 2000-01-01 04:00:00 | 39.090692 |     1.0 | 0.633368 |  0.30343 |
    | 2000-01-01 04:05:00 | 39.223815 |     1.0 | 0.637282 | 0.311352 |
    | 2000-01-01 04:10:00 | 39.355334 |     1.0 | 0.641182 | 0.319235 |
    | 2000-01-01 04:15:00 |  39.48526 |     1.0 | 0.645068 | 0.327078 |
    | 2000-01-01 04:20:00 | 39.613604 |     1.0 | 0.648937 | 0.334877 |
    | 2000-01-01 04:25:00 | 39.740379 |     1.0 | 0.652788 | 0.342631 |
    | 2000-01-01 04:30:00 | 39.865596 |     1.0 | 0.656622 | 0.350339 |
    | 2000-01-01 04:35:00 | 39.989269 |     1.0 | 0.660437 | 0.357997 |
    | 2000-01-01 04:40:00 | 40.111408 |     1.0 | 0.664232 | 0.365604 |
    | 2000-01-01 04:45:00 | 40.232028 |     1.0 | 0.668006 |  0.37316 |
    | 2000-01-01 04:50:00 | 40.351141 |     1.0 |  0.67176 | 0.380661 |
    | 2000-01-01 04:55:00 |  40.46876 |     1.0 | 0.675491 | 0.388108 |

There is no indication of an error in the water balance:

>>> round_(test.hydpy.collectives[0].model.check_waterbalance(conditions))
0.0

.. _sw1d_network_confluences:

Confluences
___________

Now, we illustrate how to build real networks by connecting more than two elements with
the same node.  We will handle the existing two subchannels as a main channel.  The one
upstream of the junction (`channel1a`) has a width of 8 mm, and the one downstream of
the junction (`channel2`) has a width of 10 m:

>>> for element, width in ([channel1a, 8.0], [channel2, 10.0]):
...     for storagemodel in element.model.storagemodels:
...         storagemodel.crosssection.parameters.control.bottomwidths(width)
...     for routingmodel in element.model.routingmodels:
...         if isinstance(routingmodel, (sw1d_lias.Model, sw1d_q_in.Model)):
...             routingmodel.crosssection.parameters.control.bottomwidths(width)

The new 10 km long side channel also consists of four segments but is only 2 m wide:

>>> channel = prepare_model("sw1d_channel")
>>> channel.parameters.control.nmbsegments(4)
>>> for i, length_ in enumerate(lengths[:4]):
...     with channel.add_storagemodel_v1(sw1d_storage, position=i):
...         length(length_)
...         with model.add_crosssection_v2("wq_trapeze"):
...             nmbtrapezes(1)
...             bottomlevels(5.0)
...             bottomwidths(2.0)
...             sideslopes(0.0)

It receives a separate inflow via another |sw1d_q_in| instance:

>>> with channel.add_routingmodel_v1(sw1d_q_in, position=0):
...     lengthdownstream(2.0)
...     timestepfactor(0.7)
...     with model.add_crosssection_v2("wq_trapeze"):
...         nmbtrapezes(1)
...         bottomlevels(5.0)
...         bottomwidths(2.0)
...         sideslopes(0.0)

We add |sw1d_lias| models for all other possible positions, including the last one:

>>> for i in range(1, 5):
...     with channel.add_routingmodel_v2(sw1d_lias, position=i):
...         lengthupstream(2.0 if i % 2 else 3.0)
...         lengthdownstream(3.0 if i % 2 else 2.0)
...         stricklercoefficient(1.0/0.03)
...         timestepfactor(0.7)
...         diffusionfactor(0.2)
...         with model.add_crosssection_v2("wq_trapeze"):
...             nmbtrapezes(1)
...             bottomlevels(5.0)
...             bottomwidths(2.0)
...             sideslopes(0.0)

So, now the |sw1d_channel| models of the elements `channel1a` and `channel1b` have
routing models at their outflow locations, and the one of element `channel2` does not
have a routing model at its inflow location.  This is the typical configuration for
modelling confluences, where one strives to couple each reach upstream of the junction
with the single reach downstream.  This setting has the effect that `channel2`
exchanges water with `channel1a` and `channel1b` directly, while `channel1a` and
`channel1b` can do so only indirectly via the first segment of `channel2`.

We assign the third channel model to another element, that we connect to a new inlet
node (for adding inflow) and to the already existing node `q_1to2` (for coupling with
the main channel):

>>> q_1b_in = Node("q_1b_in", variable="LongQ")
>>> channel1b = Element("channel1b", collective="network", inlets=q_1b_in, outlets=q_1to2)
>>> channel1b.model = channel

The initial water depth is 1 m throughout the whole network:

>>> test = IntegrationTest()
>>> prepare_inits(channel1a=1.0, channel1b=1.0, channel2=1.0)

The main and the side channels receive constant inflows of 1 and 0.5 m³/s,
respectively:

>>> q_1a_in.sequences.sim.series = 1.0
>>> q_1b_in.sequences.sim.series = 0.5

Unfortunately, the usual standard table does not provide much information for in-depth
evaluations:

.. integration-test::

    >>> conditions = test(get_conditions="2000-01-01 00:00")
    |                date |  timestep | q_1a_in | q_1b_in |   q_1to2 | q_2_out |
    ----------------------------------------------------------------------------
    | 2000-01-01 00:00:00 | 45.030299 |     1.0 |     0.5 |      0.0 |     0.0 |
    | 2000-01-01 00:05:00 | 46.242118 |     1.0 |     0.5 | 0.003008 |     0.0 |
    | 2000-01-01 00:10:00 | 47.155436 |     1.0 |     0.5 | 0.025525 |     0.0 |
    | 2000-01-01 00:15:00 | 47.892762 |     1.0 |     0.5 | 0.071726 |     0.0 |
    | 2000-01-01 00:20:00 | 48.522333 |     1.0 |     0.5 | 0.129271 |     0.0 |
    | 2000-01-01 00:25:00 | 49.080523 |     1.0 |     0.5 | 0.187172 |     0.0 |
    | 2000-01-01 00:30:00 | 49.587791 |     1.0 |     0.5 | 0.240134 |     0.0 |
    | 2000-01-01 00:35:00 | 50.056456 |     1.0 |     0.5 | 0.286648 |     0.0 |
    | 2000-01-01 00:40:00 | 50.494442 |     1.0 |     0.5 | 0.326895 |     0.0 |
    | 2000-01-01 00:45:00 |  50.90715 |     1.0 |     0.5 | 0.361611 |     0.0 |
    | 2000-01-01 00:50:00 | 51.298454 |     1.0 |     0.5 | 0.391611 |     0.0 |
    | 2000-01-01 00:55:00 | 51.671261 |     1.0 |     0.5 | 0.417633 |     0.0 |
    | 2000-01-01 01:00:00 | 52.027843 |     1.0 |     0.5 |  0.44031 |     0.0 |
    | 2000-01-01 01:05:00 | 52.370039 |     1.0 |     0.5 | 0.460176 |     0.0 |
    | 2000-01-01 01:10:00 | 52.699381 |     1.0 |     0.5 |  0.47769 |     0.0 |
    | 2000-01-01 01:15:00 | 53.017173 |     1.0 |     0.5 | 0.493237 |     0.0 |
    | 2000-01-01 01:20:00 | 53.324545 |     1.0 |     0.5 |  0.50715 |     0.0 |
    | 2000-01-01 01:25:00 | 53.622482 |     1.0 |     0.5 | 0.519705 |     0.0 |
    | 2000-01-01 01:30:00 | 53.911854 |     1.0 |     0.5 | 0.531136 |     0.0 |
    | 2000-01-01 01:35:00 | 54.193429 |     1.0 |     0.5 | 0.541633 |     0.0 |
    | 2000-01-01 01:40:00 | 54.467891 |     1.0 |     0.5 | 0.551355 |     0.0 |
    | 2000-01-01 01:45:00 | 54.735849 |     1.0 |     0.5 | 0.560428 |     0.0 |
    | 2000-01-01 01:50:00 | 54.997846 |     1.0 |     0.5 | 0.568953 |     0.0 |
    | 2000-01-01 01:55:00 | 55.254368 |     1.0 |     0.5 | 0.577012 |     0.0 |
    | 2000-01-01 02:00:00 | 55.505854 |     1.0 |     0.5 | 0.584668 |     0.0 |
    | 2000-01-01 02:05:00 | 55.752694 |     1.0 |     0.5 | 0.591971 |     0.0 |
    | 2000-01-01 02:10:00 | 55.995245 |     1.0 |     0.5 | 0.598961 |     0.0 |
    | 2000-01-01 02:15:00 | 56.233826 |     1.0 |     0.5 | 0.605669 |     0.0 |
    | 2000-01-01 02:20:00 | 56.468727 |     1.0 |     0.5 | 0.612118 |     0.0 |
    | 2000-01-01 02:25:00 | 56.700214 |     1.0 |     0.5 | 0.618328 |     0.0 |
    | 2000-01-01 02:30:00 | 56.928527 |     1.0 |     0.5 | 0.624314 |     0.0 |
    | 2000-01-01 02:35:00 | 57.153887 |     1.0 |     0.5 | 0.630087 |     0.0 |
    | 2000-01-01 02:40:00 | 57.376496 |     1.0 |     0.5 | 0.635659 |     0.0 |
    | 2000-01-01 02:45:00 |  57.59654 |     1.0 |     0.5 | 0.641038 |     0.0 |
    | 2000-01-01 02:50:00 | 57.814191 |     1.0 |     0.5 | 0.646232 |     0.0 |
    | 2000-01-01 02:55:00 | 58.029607 |     1.0 |     0.5 | 0.651246 |     0.0 |
    | 2000-01-01 03:00:00 | 58.242934 |     1.0 |     0.5 | 0.656087 |     0.0 |
    | 2000-01-01 03:05:00 |  58.45431 |     1.0 |     0.5 | 0.660761 |     0.0 |
    | 2000-01-01 03:10:00 | 58.663861 |     1.0 |     0.5 | 0.665273 |     0.0 |
    | 2000-01-01 03:15:00 | 58.871705 |     1.0 |     0.5 | 0.669628 |     0.0 |
    | 2000-01-01 03:20:00 | 59.077952 |     1.0 |     0.5 |  0.67383 |     0.0 |
    | 2000-01-01 03:25:00 | 59.282705 |     1.0 |     0.5 | 0.677885 |     0.0 |
    | 2000-01-01 03:30:00 |  59.48606 |     1.0 |     0.5 | 0.681797 |     0.0 |
    | 2000-01-01 03:35:00 | 59.688108 |     1.0 |     0.5 | 0.685571 |     0.0 |
    | 2000-01-01 03:40:00 | 59.888932 |     1.0 |     0.5 | 0.689211 |     0.0 |
    | 2000-01-01 03:45:00 |  0.135626 |     1.0 |     0.5 | 0.692729 |     0.0 |
    | 2000-01-01 03:50:00 |  0.384228 |     1.0 |     0.5 | 0.698366 |     0.0 |
    | 2000-01-01 03:55:00 |  0.632218 |     1.0 |     0.5 | 0.701582 |     0.0 |
    | 2000-01-01 04:00:00 |  0.879114 |     1.0 |     0.5 | 0.704443 |     0.0 |
    | 2000-01-01 04:05:00 |  1.124822 |     1.0 |     0.5 | 0.707155 |     0.0 |
    | 2000-01-01 04:10:00 |  1.369384 |     1.0 |     0.5 | 0.709781 |     0.0 |
    | 2000-01-01 04:15:00 |  1.612877 |     1.0 |     0.5 | 0.712341 |     0.0 |
    | 2000-01-01 04:20:00 |  1.855383 |     1.0 |     0.5 | 0.714841 |     0.0 |
    | 2000-01-01 04:25:00 |  2.096978 |     1.0 |     0.5 | 0.717279 |     0.0 |
    | 2000-01-01 04:30:00 |  2.337734 |     1.0 |     0.5 | 0.719653 |     0.0 |
    | 2000-01-01 04:35:00 |  2.577714 |     1.0 |     0.5 | 0.721961 |     0.0 |
    | 2000-01-01 04:40:00 |  2.816978 |     1.0 |     0.5 | 0.724201 |     0.0 |
    | 2000-01-01 04:45:00 |   3.05558 |     1.0 |     0.5 | 0.726373 |     0.0 |
    | 2000-01-01 04:50:00 |  3.293568 |     1.0 |     0.5 | 0.728475 |     0.0 |
    | 2000-01-01 04:55:00 |   3.53099 |     1.0 |     0.5 | 0.730509 |     0.0 |

Therefore, we define the following function for plotting the water level profiles
gained for the simulation period's end:

>>> def plot_waterlevels(figname):
...      import numpy
...      from matplotlib import pyplot
...      from hydpy.core.testtools import save_autofig
...      stations = ((cs := numpy.cumsum((0.0,) + lengths))[:-1] + cs[1:]) / 2.0
...      for element in (channel1a, channel1b, channel2):
...          ss = [s + sum(lengths) * (element is channel2) for s in stations]
...          ws = [sm.sequences.factors.waterlevel for sm in element.model.storagemodels]
...          _ = pyplot.plot(ss, ws, label=element.name)
...      for element in (channel1a, channel1b):
...          ss = stations[-1], stations[0] + sum(lengths)
...          ws = (element.model.storagemodels[-1].sequences.factors.waterlevel.value,
...                channel2.model.storagemodels[0].sequences.factors.waterlevel.value)
...          _ = pyplot.plot(ss, ws, color="grey")
...      _ = pyplot.legend()
...      _ = pyplot.xlabel("station [km]")
...      _ = pyplot.ylabel("water level [m]")
...      save_autofig(figname)

The simulated water levels look reasonable and are sufficiently similar to those we
calculated with a fully hydrodynamic model for comparison:

>>> plot_waterlevels("sw1d_network_confluences.png")

.. image:: sw1d_network_confluences.png

There is no indication of an error in the water balance:

>>> round_(test.hydpy.collectives[0].model.check_waterbalance(conditions))
0.0

.. _sw1d_network_bifurcations:

Bifurcations
____________

|sw1d_network| also allows us to model the bifurcation of channels.  We could
demonstrate this by building an entirely new setting but prefer to reuse the existing
network and just let the water flow "upstream", which is the same in the end.

First, we break the connections to the |sw1d_weir_out| submodel at the outlet location
of `channel2`:

>>> channel2.model.storagemodels[-1].routingmodelsdownstream.number = 0
>>> channel2.model.routingmodels[-2].routingmodelsdownstream.number = 0

Second, we replace the weir model with an instance of |sw1d_q_out|, which is
functionally nearly identical to |sw1d_q_in| but to be placed at outlet locations:

>>> from hydpy.models import sw1d_q_out
>>> with channel2.model.add_routingmodel_v3(sw1d_q_out, position=4):
...     lengthupstream(2.0)
...     timestepfactor(0.7)
...     with model.add_crosssection_v2("wq_trapeze"):
...         nmbtrapezes(1)
...         bottomlevels(5.0)
...         bottomwidths(5.0)
...         sideslopes(0.0)

>>> channel2.model.connect()

We set the initial conditions as in the :ref:`sw1d_network_confluences` example:

>>> test = IntegrationTest()
>>> prepare_inits(channel1a=1.0, channel1b=1.0, channel2=1.0)

We let the same amount of water flow in the opposite direction by setting the inflow of
`channel1a` and `channel1b` to zero and the outflow of `channel2` to -1.5 m³/s:

>>> q_1a_in.sequences.sim.series = 0.0
>>> q_1b_in.sequences.sim.series = 0.0
>>> q_2_out.sequences.sim.series = -1.5

The outlet node `q_2_out` needs further attention.  Usually, outlet nodes receive data
from their entry elements, but this one is supposed to send data "upstream", which is
possible by choosing one of the available "bidirectional" deploy modes.  We select
`oldsim_bi` (the documentation on |Node.deploymode| explains this and the further
options in more detail):

>>> q_2_out.deploymode = "oldsim_bi"

Considering the absolute amount, the discharge simulated at the central node `q_1to2`
is quite similar to the one of the :ref:`sw1d_network_confluences` example:

.. integration-test::

    >>> conditions = test("sw1d_network_branch", get_conditions="2000-01-01 00:00")
    |                date |  timestep | q_1a_in | q_1b_in |    q_1to2 | q_2_out |
    -----------------------------------------------------------------------------
    | 2000-01-01 00:00:00 | 44.830004 |     0.0 |     0.0 |       0.0 |    -1.5 |
    | 2000-01-01 00:05:00 | 45.741893 |     0.0 |     0.0 | -0.002955 |    -1.5 |
    | 2000-01-01 00:10:00 | 46.659139 |     0.0 |     0.0 | -0.026069 |    -1.5 |
    | 2000-01-01 00:15:00 | 47.456384 |     0.0 |     0.0 | -0.075937 |    -1.5 |
    | 2000-01-01 00:20:00 | 48.151282 |     0.0 |     0.0 | -0.140683 |    -1.5 |
    | 2000-01-01 00:25:00 | 48.772646 |     0.0 |     0.0 | -0.207348 |    -1.5 |
    | 2000-01-01 00:30:00 | 49.341144 |     0.0 |     0.0 | -0.268565 |    -1.5 |
    | 2000-01-01 00:35:00 | 49.870269 |     0.0 |     0.0 | -0.321749 |    -1.5 |
    | 2000-01-01 00:40:00 | 50.368827 |     0.0 |     0.0 | -0.366871 |    -1.5 |
    | 2000-01-01 00:45:00 | 50.842694 |     0.0 |     0.0 | -0.404905 |    -1.5 |
    | 2000-01-01 00:50:00 | 51.295919 |     0.0 |     0.0 | -0.437038 |    -1.5 |
    | 2000-01-01 00:55:00 | 51.731393 |     0.0 |     0.0 | -0.464363 |    -1.5 |
    | 2000-01-01 01:00:00 | 52.151263 |     0.0 |     0.0 | -0.487801 |    -1.5 |
    | 2000-01-01 01:05:00 | 52.557188 |     0.0 |     0.0 | -0.508095 |    -1.5 |
    | 2000-01-01 01:10:00 |   52.9505 |     0.0 |     0.0 | -0.525847 |    -1.5 |
    | 2000-01-01 01:15:00 | 53.332303 |     0.0 |     0.0 | -0.541542 |    -1.5 |
    | 2000-01-01 01:20:00 | 53.703533 |     0.0 |     0.0 |  -0.55557 |    -1.5 |
    | 2000-01-01 01:25:00 | 54.065003 |     0.0 |     0.0 | -0.568243 |    -1.5 |
    | 2000-01-01 01:30:00 | 54.417423 |     0.0 |     0.0 | -0.579812 |    -1.5 |
    | 2000-01-01 01:35:00 | 54.761425 |     0.0 |     0.0 | -0.590476 |    -1.5 |
    | 2000-01-01 01:40:00 | 55.097571 |     0.0 |     0.0 | -0.600391 |    -1.5 |
    | 2000-01-01 01:45:00 | 55.426366 |     0.0 |     0.0 | -0.609678 |    -1.5 |
    | 2000-01-01 01:50:00 | 55.748265 |     0.0 |     0.0 | -0.618434 |    -1.5 |
    | 2000-01-01 01:55:00 | 56.063683 |     0.0 |     0.0 | -0.626729 |    -1.5 |
    | 2000-01-01 02:00:00 | 56.372995 |     0.0 |     0.0 | -0.634621 |    -1.5 |
    | 2000-01-01 02:05:00 | 56.676546 |     0.0 |     0.0 | -0.642152 |    -1.5 |
    | 2000-01-01 02:10:00 | 56.974651 |     0.0 |     0.0 | -0.649356 |    -1.5 |
    | 2000-01-01 02:15:00 | 57.267603 |     0.0 |     0.0 | -0.656257 |    -1.5 |
    | 2000-01-01 02:20:00 | 57.555671 |     0.0 |     0.0 | -0.662874 |    -1.5 |
    | 2000-01-01 02:25:00 | 57.839105 |     0.0 |     0.0 | -0.669225 |    -1.5 |
    | 2000-01-01 02:30:00 | 58.118138 |     0.0 |     0.0 | -0.675321 |    -1.5 |
    | 2000-01-01 02:35:00 | 58.392989 |     0.0 |     0.0 | -0.681174 |    -1.5 |
    | 2000-01-01 02:40:00 |  58.66386 |     0.0 |     0.0 | -0.686793 |    -1.5 |
    | 2000-01-01 02:45:00 | 58.930943 |     0.0 |     0.0 | -0.692186 |    -1.5 |
    | 2000-01-01 02:50:00 | 59.194418 |     0.0 |     0.0 |  -0.69736 |    -1.5 |
    | 2000-01-01 02:55:00 | 59.454452 |     0.0 |     0.0 | -0.702325 |    -1.5 |
    | 2000-01-01 03:00:00 | 59.711205 |     0.0 |     0.0 | -0.707085 |    -1.5 |
    | 2000-01-01 03:05:00 | 59.964827 |     0.0 |     0.0 | -0.711648 |    -1.5 |
    | 2000-01-01 03:10:00 |   0.30038 |     0.0 |     0.0 | -0.716007 |    -1.5 |
    | 2000-01-01 03:15:00 |  0.611639 |     0.0 |     0.0 | -0.719329 |    -1.5 |
    | 2000-01-01 03:20:00 |   0.92016 |     0.0 |     0.0 |  -0.72384 |    -1.5 |
    | 2000-01-01 03:25:00 |  1.224742 |     0.0 |     0.0 | -0.728033 |    -1.5 |
    | 2000-01-01 03:30:00 |   1.52568 |     0.0 |     0.0 | -0.731932 |    -1.5 |
    | 2000-01-01 03:35:00 |   1.82326 |     0.0 |     0.0 | -0.735573 |    -1.5 |
    | 2000-01-01 03:40:00 |  2.117718 |     0.0 |     0.0 | -0.738988 |    -1.5 |
    | 2000-01-01 03:45:00 |  2.409252 |     0.0 |     0.0 | -0.742203 |    -1.5 |
    | 2000-01-01 03:50:00 |  2.698035 |     0.0 |     0.0 |  -0.74524 |    -1.5 |
    | 2000-01-01 03:55:00 |   2.98422 |     0.0 |     0.0 | -0.748116 |    -1.5 |
    | 2000-01-01 04:00:00 |  3.267941 |     0.0 |     0.0 | -0.750845 |    -1.5 |
    | 2000-01-01 04:05:00 |  3.549322 |     0.0 |     0.0 | -0.753437 |    -1.5 |
    | 2000-01-01 04:10:00 |  3.828473 |     0.0 |     0.0 | -0.755902 |    -1.5 |
    | 2000-01-01 04:15:00 |  4.105495 |     0.0 |     0.0 | -0.758246 |    -1.5 |
    | 2000-01-01 04:20:00 |  4.380482 |     0.0 |     0.0 | -0.760477 |    -1.5 |
    | 2000-01-01 04:25:00 |  4.653521 |     0.0 |     0.0 |   -0.7626 |    -1.5 |
    | 2000-01-01 04:30:00 |  4.924693 |     0.0 |     0.0 |  -0.76462 |    -1.5 |
    | 2000-01-01 04:35:00 |  5.194073 |     0.0 |     0.0 |  -0.76654 |    -1.5 |
    | 2000-01-01 04:40:00 |  5.461733 |     0.0 |     0.0 | -0.768366 |    -1.5 |
    | 2000-01-01 04:45:00 |  5.727738 |     0.0 |     0.0 |   -0.7701 |    -1.5 |
    | 2000-01-01 04:50:00 |  5.992153 |     0.0 |     0.0 | -0.771747 |    -1.5 |
    | 2000-01-01 04:55:00 |  6.255037 |     0.0 |     0.0 |  -0.77331 |    -1.5 |

Again, the simulated water levels at the end of the simulation period seem reasonable
and sufficiently similar to those we calculated with a fully hydrodynamic model:

>>> plot_waterlevels("sw1d_network_bifurcations.png")

.. image:: sw1d_network_bifurcations.png

There is no indication of an error in the water balance:

>>> round_(test.hydpy.collectives[0].model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from standard library
from __future__ import annotations

# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.exe.modelimports import *
from hydpy.interfaces import routinginterfaces

# ...from sw1d
from hydpy.models.sw1d import sw1d_model
from hydpy.models.sw1d import sw1d_derived
from hydpy.models import sw1d_channel

ADDITIONAL_DERIVEDPARAMETERS = (sw1d_derived.Seconds,)


class Model(modeltools.SubstepModel):
    """A "composite model" for solving the 1-dimensional shallow water equations in
    complex channel networks."""

    COMPOSITE = True
    """|sw1d_network| is a composite model.  (One usually only works with it 
    indirectly.)"""

    INLET_METHODS = (sw1d_model.Trigger_Preprocessing_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        sw1d_model.Calc_MaxTimeSteps_V1,
        sw1d_model.Calc_TimeStep_V1,
        sw1d_model.Send_TimeStep_V1,
        sw1d_model.Calc_Discharges_V1,
        sw1d_model.Update_Storages_V1,
    )
    INTERFACE_METHODS = ()
    ADD_METHODS = ()
    OUTLET_METHODS = (sw1d_model.Trigger_Postprocessing_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.RoutingModel_V3,
        routinginterfaces.StorageModel_V1,
        routinginterfaces.ChannelModel_V1,
    )
    SUBMODELS = ()

    channelmodels = modeltools.SubmodelsProperty(routinginterfaces.ChannelModel_V1)
    storagemodels = modeltools.SubmodelsProperty(routinginterfaces.StorageModel_V1)
    routingmodels = modeltools.SubmodelsProperty(
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.RoutingModel_V3,
    )

    def check_waterbalance(self, initial_conditions: ConditionsModel) -> float:
        r"""Determine the water balance error of the previous simulation in 1000 m³.

        Method |Model.check_waterbalance| calculates the balance error as follows:

          .. math::
            Error =  \Sigma In - \Sigma Out + \Sigma Lat - \Delta Vol \\
            \\
            \Sigma In = \sum_{t=t_0}^{t_1} \sum_{i=1}^{R_1} DischargeVolume_t^i  \\
            \Sigma Out = \sum_{t=t_0}^{t_1} \sum_{i=1}^{R_3} DischargeVolume_t^i  \\
            \Sigma Lat = Seconds \cdot
            \sum_{t=t_0}^{t_1} \sum_{i=1}^{S_1} LateralFlow_t^i \\
            \Delta Vol = 1000 \cdot
            \sum_{i=1}^{S_1} WaterVolume_{t_1}^i - WaterVolume_{t_0}^i \\
            \\
            S_1 = N(StorageModel\_V1) \\
            R_1 = N(RoutingModel\_V1) \\
            R_3 = N(RoutingModel\_V3)

        The returned error should always be in scale with numerical precision so that
        it does not affect the simulation results in any relevant manner.

        Pick the required initial conditions before starting the simulation run via
        property |Sequences.conditions|.  See the application model |sw1d_network| for
        integration tests some examples.

        ToDo: So far, |Model.check_waterbalance| works only safely with application
              models |sw1d_storage|, |sw1d_q_in|, |sw1d_lias|, |sw1d_q_out|, and
              |sw1d_weir_out| and might fail for other models.  We need to implement a
              more general solution when we implement incompatible models.
        """

        r1 = routinginterfaces.RoutingModel_V1
        r3 = routinginterfaces.RoutingModel_V3
        r2 = routinginterfaces.RoutingModel_V2
        v2 = routinginterfaces.ChannelModel_V1

        secs = self.parameters.derived.seconds.value
        volume_old, volume_new, latflow = 0.0, 0.0, 0.0
        inflow, outflow = 0.0, 0.0
        for name, model in self.find_submodels(include_subsubmodels=False).items():
            if isinstance(model, routinginterfaces.StorageModel_V1):
                wv = initial_conditions[name]["states"]["watervolume"]
                assert isinstance(wv, float)
                volume_old += 1000.0 * wv
                volume_new += 1000.0 * model.sequences.states.watervolume
                latflow += secs * numpy.sum(model.sequences.fluxes.lateralflow.series)
            elif isinstance(model, r1):
                inflow += numpy.sum(model.sequences.fluxes.dischargevolume.series)
            elif isinstance(model, r3):
                outflow += numpy.sum(model.sequences.fluxes.dischargevolume.series)
            else:
                assert isinstance(model, (r2, v2))
        return volume_old + inflow - outflow + latflow - volume_new


@modeltools.define_modelcoupler(inputtypes=(sw1d_channel.Model,), outputtype=Model)
def combine_channels(
    *, nodes: devicetools.Nodes, elements: devicetools.Elements
) -> Model:
    """Combine all the submodels of the given |sw1d_channel| instances within a new
    |sw1d_network| instance and build their missing connections.

    |combine_channels| has to address many corner cases, especially for discovering
    configuration errors.  We define a helper function that returns a (hopefully
    sufficiently complex) valid setting containing six |sw1d_channel| models, including
    one bifurcation and one confluence:

    >>> from hydpy import Element, Nodes, prepare_model
    >>> def prepare_example():
    ...
    ...     nodes = n12, n23, n34, n45 = Nodes("n12", "n23", "n34", "n45",
    ...                                        defaultvariable="LongQ")
    ...
    ...     e1 = Element("e1", outlets=n12)
    ...     e2 = Element("e2", inlets=n12, outlets=n23)
    ...     e3a = Element("e3a", inlets=n23, outlets=n34)
    ...     e3b = Element("e3b", inlets=n23, outlets=n34)
    ...     e4 = Element("e4", inlets=n34, outlets=n45)
    ...     e5 = Element("e5", inlets=n45)
    ...     elements = e1, e2, e3a, e3b, e4, e5
    ...
    ...     m1 = prepare_model("sw1d_channel")
    ...     m2 = prepare_model("sw1d_channel")
    ...     m3a = prepare_model("sw1d_channel")
    ...     m3b = prepare_model("sw1d_channel")
    ...     m4 = prepare_model("sw1d_channel")
    ...     m5 = prepare_model("sw1d_channel")
    ...     models = m1, m2, m3a, m3b, m4, m5
    ...
    ...     m1.parameters.control.nmbsegments(1)
    ...     m2.parameters.control.nmbsegments(1)
    ...     m3a.parameters.control.nmbsegments(2)
    ...     m3b.parameters.control.nmbsegments(1)
    ...     m4.parameters.control.nmbsegments(1)
    ...     m5.parameters.control.nmbsegments(1)
    ...
    ...     for m in models:
    ...         for i in range(m.parameters.control.nmbsegments.value):
    ...             with m.add_storagemodel_v1("sw1d_storage", position=i):
    ...                 pass
    ...     for m, ps in ((m1, [1]), (m3a, [0, 1, 2]), (m3b, [0, 1]), (m5, [0])):
    ...         for p in ps:
    ...             with m.add_routingmodel_v2("sw1d_lias", position=p, update=False):
    ...                 pass
    ...
    ...     e1.model = m1
    ...     e2.model = m2
    ...     e3a.model = m3a
    ...     e3b.model = m3b
    ...     e4.model = m4
    ...     e5.model = m5
    ...
    ...     return nodes, elements, models

    The second helper function checks for this example if all |combine_channels| builds
    all side-model connections correctly and does not break already existing ones:

    >>> def apply_assertions(models):
    ...     m1, m2, m3a, m3b, m4, m5 = models
    ...
    ...     sm = m1.storagemodels[0]
    ...     assert (rmsd := sm.routingmodelsdownstream).number == 1
    ...     assert m1.routingmodels[1] in rmsd
    ...
    ...     rm = m1.routingmodels[1]
    ...     assert rm.routingmodelsupstream.number == 0
    ...     assert rm.storagemodelupstream is m1.storagemodels[0]
    ...     assert rm.storagemodeldownstream is m2.storagemodels[0]
    ...     assert (rmsd := rm.routingmodelsdownstream).number == 2
    ...     assert m3a.routingmodels[0] in rmsd
    ...     assert m3b.routingmodels[0] in rmsd
    ...
    ...     sm = m2.storagemodels[0]
    ...     assert (rmsu := sm.routingmodelsupstream).number == 1
    ...     assert m1.routingmodels[1] in rmsu
    ...     assert (rmsd := sm.routingmodelsdownstream).number == 2
    ...     assert m3a.routingmodels[0] in rmsd
    ...     assert m3a.routingmodels[0] in rmsd
    ...
    ...     rm = m3a.routingmodels[0]
    ...     assert (rmsu := rm.routingmodelsupstream).number == 1
    ...     assert m1.routingmodels[1] in rmsu
    ...     assert rm.storagemodelupstream is m2.storagemodels[0]
    ...     assert rm.storagemodeldownstream is m3a.storagemodels[0]
    ...     assert (rmsd := rm.routingmodelsdownstream).number == 1
    ...     assert m3a.routingmodels[1] in rmsd
    ...
    ...     sm = m3a.storagemodels[0]
    ...     assert (rmsu := sm.routingmodelsupstream).number == 1
    ...     assert m3a.routingmodels[0] in rmsu
    ...     assert (rmsd := sm.routingmodelsdownstream).number == 1
    ...     assert m3a.routingmodels[1] in rmsd
    ...
    ...     rm = m3a.routingmodels[1]
    ...     assert (rmsu := rm.routingmodelsupstream).number == 1
    ...     assert m3a.routingmodels[0] in rmsu
    ...     assert rm.storagemodelupstream is m3a.storagemodels[0]
    ...     assert rm.storagemodeldownstream is m3a.storagemodels[1]
    ...     assert (rmsd := rm.routingmodelsdownstream).number == 1
    ...     assert m3a.routingmodels[2] in rmsd
    ...
    ...     sm = m3a.storagemodels[1]
    ...     assert (rmsu := sm.routingmodelsupstream).number == 1
    ...     assert m3a.routingmodels[1] in rmsu
    ...     assert (rmsd := sm.routingmodelsdownstream).number == 1
    ...     assert m3a.routingmodels[2] in rmsd
    ...
    ...     rm = m3a.routingmodels[2]
    ...     assert (rmsu := rm.routingmodelsupstream).number == 1
    ...     assert m3a.routingmodels[1] in rmsu
    ...     assert rm.storagemodelupstream is m3a.storagemodels[1]
    ...     assert rm.storagemodeldownstream is m4.storagemodels[0]
    ...     assert (rmsd := rm.routingmodelsdownstream).number == 1
    ...     assert m5.routingmodels[0] in rmsd
    ...
    ...     rm = m3b.routingmodels[0]
    ...     assert (rmsu := rm.routingmodelsupstream).number == 1
    ...     assert m1.routingmodels[1] in rmsu
    ...     assert rm.storagemodelupstream is m2.storagemodels[0]
    ...     assert rm.storagemodeldownstream is m3b.storagemodels[0]
    ...     assert (rmsd := rm.routingmodelsdownstream).number == 1
    ...     assert m3b.routingmodels[1] in rmsd
    ...
    ...     sm = m3b.storagemodels[0]
    ...     assert (rmsu := sm.routingmodelsupstream).number == 1
    ...     assert m3b.routingmodels[0] in rmsu
    ...     assert (rmsd := sm.routingmodelsdownstream).number == 1
    ...     assert m3b.routingmodels[1] in rmsd
    ...
    ...     rm = m3b.routingmodels[1]
    ...     assert (rmsu := rm.routingmodelsupstream).number == 1
    ...     assert m3b.routingmodels[0] in rmsu
    ...     assert rm.storagemodelupstream is m3b.storagemodels[0]
    ...     assert rm.storagemodeldownstream is m4.storagemodels[0]
    ...     assert (rmsd := rm.routingmodelsdownstream).number == 1
    ...     assert m5.routingmodels[0] in rmsd
    ...
    ...     sm = m4.storagemodels[0]
    ...     assert (rmsu := sm.routingmodelsupstream).number == 2
    ...     assert m3a.routingmodels[2] in rmsu
    ...     assert m3b.routingmodels[1] in rmsu
    ...     assert (rmsd := sm.routingmodelsdownstream).number == 1
    ...     assert m5.routingmodels[0] in rmsd
    ...
    ...     rm = m5.routingmodels[0]
    ...     assert (rmsu := rm.routingmodelsupstream).number == 2
    ...     assert m3a.routingmodels[2] in rmsu
    ...     assert m3b.routingmodels[1] in rmsu
    ...     assert rm.storagemodelupstream is m4.storagemodels[0]
    ...     assert rm.storagemodeldownstream is m5.storagemodels[0]
    ...     assert (rmsd := rm.routingmodelsdownstream).number == 0
    ...
    ...     sm = m5.storagemodels[0]
    ...     assert (rmsu := sm.routingmodelsupstream).number == 1
    ...     assert m5.routingmodels[0] in rmsu
    ...     assert (rmsd := sm.routingmodelsdownstream).number == 0

    According to the test functions, |combine_channels| works correctly:

    >>> nodes, elements, models = prepare_example()
    >>> from hydpy.models.sw1d_network import combine_channels
    >>> network = combine_channels(nodes=nodes, elements=elements)
    >>> apply_assertions(models)

    Before building new connections, |combine_channels| deletes existing ones that it
    is responsible for and might have ,ade in an earlier call.  This preprocessing step
    allows to use |combine_channels| multiple times without risking duplicate
    connections:

    >>> network = combine_channels(nodes=nodes, elements=elements)
    >>> apply_assertions(models)

    |combine_channels| performs various checks.  We shortly explain the covered
    configuration errors.

    There must be one routing model between all neighbouring segments of a single
    channel:

    >>> models[2].routingmodels.delete_submodel(1)
    >>> combine_channels(nodes=nodes, elements=elements)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to couple the given model instances to a composite \
model of type `sw1d_network` based on function `combine_channels`, the following \
error occurred: Model `sw1d_channel` of element `e3a` requires a routing model at \
position `1`, which is missing.

    There must be one storage model for each channel segment:

    >>> models[1].storagemodels.delete_submodel(0)
    >>> combine_channels(nodes=nodes, elements=elements)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: ... Model `sw1d_channel` of element `e2` requires a storage model \
at position `0`, which is missing.

    There must be one routing model between each pair of a channel's neighbouring
    segments:

    >>> nodes, elements, models = prepare_example()
    >>> models[5].routingmodels.delete_submodel(0)
    >>> combine_channels(nodes=nodes, elements=elements)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: ... Either model `sw1d_channel` of element `e4` requires a routing \
model at its last position or model `sw1d_channel` of element `e5` at its first \
position, but both are missing.

    All routing models between two segments must allow building connections to upstream
    models:

    >>> with models[5].add_routingmodel_v1("sw1d_q_in", position=0, update=False):
    ...     pass
    >>> elements[5].model = models[5]
    >>> combine_channels(nodes=nodes, elements=elements)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: ... Submodel `sw1d_q_in` of element `e5` does not allow to build an \
upstream connection to model `sw1d_channel` of element `e4`.

    All routing models between two segments must allow building connections to
    downstream models:

    >>> with models[0].add_routingmodel_v3("sw1d_q_out", position=1, update=False):
    ...     pass
    >>> elements[0].model = models[0]
    >>> combine_channels(nodes=nodes, elements=elements)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: ... Submodel `sw1d_q_out` of element `e1` does not allow to build \
a downstream connection to model `sw1d_channel` of element `e2`.

    There cannot be multiple routing models between two segments:

    >>> nodes, elements, models = prepare_example()
    >>> with models[4].add_routingmodel_v2("sw1d_lias", position=1, update=False):
    ...     pass
    >>> combine_channels(nodes=nodes, elements=elements)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: ... Either model `sw1d_channel` of element `e4` must provide a \
routing model at its last position or model `sw1d_channel` of element `e5` at its \
first position, but both do.

    One cannot connect a routing model to multiple upstream storage models:

    >>> models[2].routingmodels.delete_submodel(2)
    >>> models[3].routingmodels.delete_submodel(1)
    >>> with models[4].add_routingmodel_v2("sw1d_lias", position=0, update=False):
    ...     pass
    >>> elements[4].model = models[4]
    >>> combine_channels(nodes=nodes, elements=elements)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: ... The first routing submodel, `sw1d_lias` of element `e4`, can \
only be connected to one upstream storage submodel but is requested to be at least \
connected to `sw1d_storage` of element `e3a` and `sw1d_storage` of element `e3b`.

    One cannot connect a routing model to multiple downstream storage models:

    >>> models[2].routingmodels.delete_submodel(0)
    >>> models[3].routingmodels.delete_submodel(0)
    >>> with models[1].add_routingmodel_v2("sw1d_lias", position=1, update=False):
    ...     pass
    >>> elements[1].model = models[1]
    >>> combine_channels(nodes=nodes, elements=elements)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: ... The last routing submodel, `sw1d_lias` of element `e2`, can \
only be connected to one downstream storage submodel but is requested to be at least \
connected to `sw1d_storage` of element `e3a` and `sw1d_storage` of element `e3b`.
    """
    # pylint: disable=too-many-nested-blocks,too-many-branches,too-many-statements

    c1 = routinginterfaces.ChannelModel_V1
    r1 = routinginterfaces.RoutingModel_V1
    r2 = routinginterfaces.RoutingModel_V2
    r3 = routinginterfaces.RoutingModel_V3
    network = importtools.prepare_model("sw1d_network")
    assert isinstance(network, Model)
    channelmodels = network.channelmodels
    storagemodels = network.storagemodels
    routingmodels = network.routingmodels
    ep = objecttools.elementphrase

    for element in elements:
        cm = element.model
        assert isinstance(cm, c1)

        # First check if all definitely required submodels are actually available:
        for i, sm in enumerate(cm.storagemodels):
            if sm is None:
                raise RuntimeError(
                    f"Model {ep(cm)} requires a storage model at position `{i}`, "
                    f"which is missing."
                )
        for i, rm in enumerate(cm.routingmodels.submodels[1:-1]):
            if rm is None:
                raise RuntimeError(
                    f"Model {ep(cm)} requires a routing model at position `{i + 1}`, "
                    f"which is missing."
                )

        # Link the network to its submodels:
        channelmodels.append_submodel(submodel=cm)
        for sm in cm.storagemodels.submodels:
            if sm is not None:
                storagemodels.append_submodel(submodel=sm)
        for rm in cm.routingmodels.submodels:
            if rm is not None:
                routingmodels.append_submodel(submodel=rm)

        # Prevent duplicate links when calling `combine_channels` twice:
        if (r_d1 := cm.routingmodels[0]) is None:
            assert (sm := cm.storagemodels[0]) is not None
            sm.routingmodelsupstream.number = 0
            if (r_d2 := cm.routingmodels[1]) is not None:
                if isinstance(r_d2, (r2, r3)):
                    r_d2.routingmodelsupstream.number = 0
                else:
                    assert not isinstance(r_d2, r1)
                    assert_never(r_d2)
        else:
            if isinstance(r_d1, r2):
                r_d1.routingmodelsupstream.number = 0
                r_d1.storagemodelupstream = None
                r_d1.storagemodelupstream_typeid = 0
            elif isinstance(r_d1, r1):
                pass
            else:
                assert not isinstance(r_d1, r3)
                assert_never(r_d1)

        if (r_u1 := cm.routingmodels[-1]) is None:
            assert (sm := cm.storagemodels[-1]) is not None
            sm.routingmodelsdownstream.number = 0
            if (r_u2 := cm.routingmodels[-2]) is not None:
                if isinstance(r_u2, (r1, r2)):
                    r_u2.routingmodelsdownstream.number = 0
                else:
                    assert not isinstance(r_u2, r3)
                    assert_never(r_u2)
        else:
            if isinstance(r_u1, r2):
                r_u1.routingmodelsdownstream.number = 0
                r_u1.storagemodeldownstream = None
                r_u1.storagemodeldownstream_typeid = 0
            elif isinstance(r_u1, r3):
                pass
            else:
                assert not isinstance(r_u1, r1)
                assert_never(r_u1)

    # Link the submodels at the channel end points:
    for node in nodes:
        for e_up in (e_up for e_up in node.entries if e_up in elements):
            assert isinstance(c_u := e_up.model, c1)
            if (r_u := c_u.routingmodels[-1]) is None:
                for e_down in (e_down for e_down in node.exits if e_down in elements):
                    assert isinstance(c_d := e_down.model, c1)
                    assert (s_u := c_u.storagemodels[-1]) is not None
                    if (r_d := c_d.routingmodels[0]) is None:
                        raise RuntimeError(
                            f"Either model {ep(c_u)} requires a routing model at its "
                            f"last position or model {ep(c_d)} at its first position, "
                            f"but both are missing."
                        )
                    if isinstance(r_d, r2):
                        pass
                    elif isinstance(r_d, r1):
                        raise RuntimeError(
                            f"Submodel {ep(r_d)} does not allow to build an upstream "
                            f"connection to model {ep(c_u)}."
                        )
                    else:
                        assert not isinstance(r_d, r3)
                        assert_never(r_d)
                    if r_d.storagemodelupstream is not None:
                        raise RuntimeError(
                            f"The first routing submodel, {ep(r_d)}, can only be "
                            f"connected to one upstream storage submodel but is "
                            f"requested to be at least connected to "
                            f"{ep(r_d.storagemodelupstream)} and {ep(s_u)}."
                        )
                    r_d.storagemodelupstream = s_u
                    r_d.storagemodelupstream_typeid = c_u.storagemodels.typeids[-1]
                    s_u.routingmodelsdownstream.append_submodel(r_d)
                    if (r_uu := c_u.routingmodels[-2]) is None:
                        # hint: this "None part" does not need to be repeated below
                        n_u = e_up.inlets[0]
                        for e_uu in (e_uu for e_uu in n_u.entries if e_uu in elements):
                            assert isinstance(c_uu := e_uu.model, c1)
                            if (r_uu := c_uu.routingmodels[-1]) is not None:
                                # hint: exception for the None case handled above
                                if isinstance(r_uu, r2):
                                    pass
                                else:
                                    assert not isinstance(r_uu, (r1, r3))
                                    assert_never(r_uu)
                                r_d.routingmodelsupstream.append_submodel(r_uu)
                                r_uu.routingmodelsdownstream.append_submodel(r_d)
                    else:
                        if isinstance(r_uu, (r1, r2)):
                            r_d.routingmodelsupstream.append_submodel(r_uu)
                            r_uu.routingmodelsdownstream.append_submodel(r_d)
                        else:
                            assert not isinstance(r_uu, r3)
                            assert_never(r_uu)
            else:
                for e_down in (e_down for e_down in node.exits if e_down in elements):
                    assert isinstance(c_d := e_down.model, c1)
                    if c_d.routingmodels[0] is not None:
                        raise RuntimeError(
                            f"Either model {ep(c_u)} must provide a routing model at "
                            f"its last position or model {ep(c_d)} at its first "
                            f"position, but both do."
                        )

        for e_down in (e_down for e_down in node.exits if e_down in elements):
            assert isinstance(c_d := e_down.model, c1)
            if (r_d := c_d.routingmodels[0]) is None:
                for e_up in (e_up for e_up in node.entries if e_up in elements):
                    assert isinstance(c_u := e_up.model, c1)
                    assert (s_d := c_d.storagemodels[0]) is not None
                    assert (r_u := c_u.routingmodels[-1]) is not None
                    if isinstance(r_u, r3):
                        raise RuntimeError(
                            f"Submodel {ep(r_u)} does not allow to build a "
                            f"downstream connection to model {ep(c_d)}."
                        )
                    assert not isinstance(r_u, r1)
                    if r_u.storagemodeldownstream is not None:
                        raise RuntimeError(
                            f"The last routing submodel, {ep(r_u)}, can only be "
                            f"connected to one downstream storage submodel but is "
                            f"requested to be at least connected to "
                            f"{ep(r_u.storagemodeldownstream)} and {ep(s_d)}."
                        )
                    r_u.storagemodeldownstream = s_d
                    r_u.storagemodeldownstream_typeid = c_d.storagemodels.typeids[0]
                    s_d.routingmodelsupstream.append_submodel(r_u)
                    if (r_dd := c_d.routingmodels[1]) is not None:
                        # hint: the "None part" is already handled above
                        if isinstance(r_dd, (r2, r3)):
                            r_u.routingmodelsdownstream.append_submodel(r_dd)
                            r_dd.routingmodelsupstream.append_submodel(r_u)
                        else:
                            assert not isinstance(r_dd, r1)
                            assert_never(r_dd)

    return network


tester = Tester()
cythonizer = Cythonizer()
