# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""

The *HydPy-Musk* model family member |musk_classic| realises the well-known Muskingum
routing method :cite:p:`ref-McCarthy1940`.  The Muskingum method is a simple
"hydrological" routing approach that applies a finite difference approximation of the
continuity equation with fixed coefficients.  Users are free to define these
coefficients manually or let |musk_classic| calculate them based on the travel time `k`
and the weighting coefficient `x` (see the documentation on parameter |Coefficients|
for further information).  Either way, one should note these coefficients apply to each
channel segment.  Hence, when increasing the number of segments (via parameter
|NmbSegments|), the net travel time through the whole channel increases, too.

|musk_classic| also supports a simplified version of the Muskingum method that is part
of HBV96 :cite:p:`ref-Lindstrom1997HBV96` and relies on the parameters `lag`,
describing lag time, and `damp`, describing the damping of the hydrograph along the
channel.  See the documentation on the parameters |NmbSegments| and |Coefficients| on
how to use this information to calculate the coefficients of the Muskingum working
equation.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 20 hours:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "01.01.2000 00:00", "01.01.2000 20:00", "1h"

We also set the time step size of the parameter values defined below to one hour:

>>> from hydpy.models.musk_classic import *
>>> parameterstep("1h")

The |musk_classic| model, handled by |Element| `stream`, queries its inflow from two
|Node| objects (`input1` and `input2`) and passes its outflow to a single |Node| object
(`output`):

>>> nodes = Nodes("input1", "input2", "output")
>>> stream = Element("stream", inlets=["input1", "input2"], outlets="output")
>>> stream.model = model

The test function object sets the initial flow into all segment endpoints
(|musk_states.Q|) to zero before each simulation run:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(stream, inits=((states.q, 0.0),))
>>> test.dateformat = "%H:%M"

We define two flood events, one for each inflow node:

>>> nodes.input1.sequences.sim.series = [
...     0.0, 0.0, 1.0, 3.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
>>> nodes.input2.sequences.sim.series = [
...     0.0, 1.0, 5.0, 9.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.0,
...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

Because of its good clarity, we use the *HBV96* style to configure the coefficients of
the working equation in all integration tests.

Zero lag time
_____________

With zero lag time, there are no river segments.   Hence, there is only one segment
endpoint, which lies both at the whole channel's start and end.  Accordingly, the
outflow is always equal to the inflow, regardless of the values chosen for the
Muskingum coefficients:

.. integration-test::

    >>> nmbsegments(lag=0.0)
    >>> coefficients(damp=1.0)
    >>> test("musk_classic_zero_lag time")
    |  date |    q | input1 | input2 | output |
    -------------------------------------------
    | 00:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 01:00 |  1.0 |    0.0 |    1.0 |    1.0 |
    | 02:00 |  6.0 |    1.0 |    5.0 |    6.0 |
    | 03:00 | 12.0 |    3.0 |    9.0 |   12.0 |
    | 04:00 | 10.0 |    2.0 |    8.0 |   10.0 |
    | 05:00 |  6.0 |    1.0 |    5.0 |    6.0 |
    | 06:00 |  3.0 |    0.0 |    3.0 |    3.0 |
    | 07:00 |  2.0 |    0.0 |    2.0 |    2.0 |
    | 08:00 |  1.0 |    0.0 |    1.0 |    1.0 |
    | 09:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 10:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 11:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 12:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 13:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 14:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 15:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 16:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 17:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 18:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 19:00 |  0.0 |    0.0 |    0.0 |    0.0 |

Translation
___________

With a lag time of three hours and zero damping, |musk_classic| simply passes the flow
values from one segment to the next within each simulation time step.  A number of
three segments gives an overall time shift of three hours:

.. integration-test::

    >>> nmbsegments(lag=3.0)
    >>> coefficients(damp=0.0)
    >>> test("musk_classic_no_translation")
    |  date |                      q | input1 | input2 | output |
    -------------------------------------------------------------
    | 00:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 01:00 |  1.0   0.0   0.0   0.0 |    0.0 |    1.0 |    0.0 |
    | 02:00 |  6.0   1.0   0.0   0.0 |    1.0 |    5.0 |    0.0 |
    | 03:00 | 12.0   6.0   1.0   0.0 |    3.0 |    9.0 |    0.0 |
    | 04:00 | 10.0  12.0   6.0   1.0 |    2.0 |    8.0 |    1.0 |
    | 05:00 |  6.0  10.0  12.0   6.0 |    1.0 |    5.0 |    6.0 |
    | 06:00 |  3.0   6.0  10.0  12.0 |    0.0 |    3.0 |   12.0 |
    | 07:00 |  2.0   3.0   6.0  10.0 |    0.0 |    2.0 |   10.0 |
    | 08:00 |  1.0   2.0   3.0   6.0 |    0.0 |    1.0 |    6.0 |
    | 09:00 |  0.0   1.0   2.0   3.0 |    0.0 |    0.0 |    3.0 |
    | 10:00 |  0.0   0.0   1.0   2.0 |    0.0 |    0.0 |    2.0 |
    | 11:00 |  0.0   0.0   0.0   1.0 |    0.0 |    0.0 |    1.0 |
    | 12:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 13:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 14:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 15:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 16:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 17:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 18:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |
    | 19:00 |  0.0   0.0   0.0   0.0 |    0.0 |    0.0 |    0.0 |

Diffusion
_________

Parameter |Coefficients| controls flood waves' diffusion (or damping) within each river
segment.  We demonstrate its functioning by keeping the `lag` value of three hours but
setting `damp` to one:

.. integration-test::

    >>> nmbsegments(lag=3.0)
    >>> coefficients(damp=1.0)
    >>> test("musk_classic_ex4")
    |  date |                                  q | input1 | input2 |   output |
    ---------------------------------------------------------------------------
    | 00:00 |  0.0       0.0       0.0       0.0 |    0.0 |    0.0 |      0.0 |
    | 01:00 |  1.0       0.5      0.25     0.125 |    0.0 |    1.0 |    0.125 |
    | 02:00 |  6.0      3.25      1.75    0.9375 |    1.0 |    5.0 |   0.9375 |
    | 03:00 | 12.0     7.625    4.6875    2.8125 |    3.0 |    9.0 |   2.8125 |
    | 04:00 | 10.0    8.8125      6.75   4.78125 |    2.0 |    8.0 |  4.78125 |
    | 05:00 |  6.0   7.40625  7.078125  5.929688 |    1.0 |    5.0 | 5.929688 |
    | 06:00 |  3.0  5.203125  6.140625  6.035156 |    0.0 |    3.0 | 6.035156 |
    | 07:00 |  2.0  3.601562  4.871094  5.453125 |    0.0 |    2.0 | 5.453125 |
    | 08:00 |  1.0  2.300781  3.585938  4.519531 |    0.0 |    1.0 | 4.519531 |
    | 09:00 |  0.0  1.150391  2.368164  3.443848 |    0.0 |    0.0 | 3.443848 |
    | 10:00 |  0.0  0.575195   1.47168  2.457764 |    0.0 |    0.0 | 2.457764 |
    | 11:00 |  0.0  0.287598  0.879639  1.668701 |    0.0 |    0.0 | 1.668701 |
    | 12:00 |  0.0  0.143799  0.511719   1.09021 |    0.0 |    0.0 |  1.09021 |
    | 13:00 |  0.0  0.071899  0.291809   0.69101 |    0.0 |    0.0 |  0.69101 |
    | 14:00 |  0.0   0.03595  0.163879  0.427444 |    0.0 |    0.0 | 0.427444 |
    | 15:00 |  0.0  0.017975  0.090927  0.259186 |    0.0 |    0.0 | 0.259186 |
    | 16:00 |  0.0  0.008987  0.049957  0.154572 |    0.0 |    0.0 | 0.154572 |
    | 17:00 |  0.0  0.004494  0.027225  0.090899 |    0.0 |    0.0 | 0.090899 |
    | 18:00 |  0.0  0.002247  0.014736  0.052817 |    0.0 |    0.0 | 0.052817 |
    | 19:00 |  0.0  0.001123   0.00793  0.030374 |    0.0 |    0.0 | 0.030374 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import masktools
from hydpy.core import modeltools

# ...from musk
from hydpy.models.musk import musk_masks
from hydpy.models.musk import musk_model


class Model(modeltools.AdHocModel):
    """The classic, fixed parameter version of HydPy-Musk (|musk_classic|)."""

    INLET_METHODS = (musk_model.Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (musk_model.Calc_Q_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = (musk_model.Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()


class Masks(masktools.Masks):
    """Masks applicable to |musk_classic|."""

    CLASSES = musk_masks.Masks.CLASSES


tester = Tester()
cythonizer = Cythonizer()
