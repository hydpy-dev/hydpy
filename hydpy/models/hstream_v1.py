# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""
Version 1 of The HydPy-H-Stream model is a straightforward routing
approach.  It applies the working equation of the Muskingum method on some
river segments of the same length.  The number of segments (parameter
|NmbSegments|) controls translation (parameter |Lag|), the Muskingum
coefficients (parameters |C1|, |C2|, and |C3|) control attenuation
(parameter |Damp|).  For |NmbSegments| only integer values are allowed,
which is why the translation time cannot be varied continuously.

Integration tests
=================

    .. how_to_understand_integration_tests::

    We perform the following examples over a simulation period of 20 hours:

    >>> from hydpy import pub, Nodes, Element
    >>> pub.timegrids = "01.01.2000 00:00", "01.01.2000 20:00", "1h"

    We also set the time step size of the parameter values defined
    below to one hour:

    >>> from hydpy.models.hstream_v1 import *
    >>> parameterstep("1h")

    The |hstream_v1| model, handled by |Element| `stream`, queries its
    inflow from two |Node| objects (`input1` and `input2`) and passes its
    outflow to a single |Node| object (`output`):

    >>> nodes = Nodes("input1", "input2", "output")
    >>> stream = Element("stream",
    ...                  inlets=["input1", "input2"],
    ...                  outlets="output")
    >>> stream.model = model

    The test function object sets the initial inflow of all segments
    junctions (|QJoints|) to zero before each simulation run:

    >>> from hydpy.core.testtools import IntegrationTest
    >>> test = IntegrationTest(stream,
    ...                        inits=((states.qjoints, 0.),))
    >>> test.dateformat = "%H:%M"

    We define two flood events, one for each inflow node:

    >>> nodes.input1.sequences.sim.series = [
    ...                     0., 0., 1., 3., 2., 1., 0., 0., 0., 0.,
    ...                     0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    >>> nodes.input2.sequences.sim.series = [
    ...                     0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...                     0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]

    **Example 1**

    With zero |Lag| time, there are no river segments.  Hence, there is
    only one "virtual" junction, which is both the start and the end
    point of the whole channel. Accordingly, outflow is always equal to
    inflow:

    >>> lag(0.0)
    >>> damp(0.0)
    >>> test("hstream_v1_ex1")
    |  date | qjoints | input1 | input2 | output |
    ----------------------------------------------
    | 00:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 01:00 |     1.0 |    0.0 |    1.0 |    1.0 |
    | 02:00 |     6.0 |    1.0 |    5.0 |    6.0 |
    | 03:00 |    12.0 |    3.0 |    9.0 |   12.0 |
    | 04:00 |    10.0 |    2.0 |    8.0 |   10.0 |
    | 05:00 |     6.0 |    1.0 |    5.0 |    6.0 |
    | 06:00 |     3.0 |    0.0 |    3.0 |    3.0 |
    | 07:00 |     2.0 |    0.0 |    2.0 |    2.0 |
    | 08:00 |     1.0 |    0.0 |    1.0 |    1.0 |
    | 09:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 10:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 11:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 12:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 13:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 14:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 15:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 16:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 17:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 18:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 19:00 |     0.0 |    0.0 |    0.0 |    0.0 |

    .. raw:: html

        <a
            href="hstream_v1_ex1.html"
            target="_blank"
        >Click here to see the graph</a>

    **Example 2**

    Parameter |Damp| controls the attenuation of flood waves within a
    single river segment.  With a zero |Lag| time, there are no river
    segments and thus not damping even for the highest possible value
    of |Damp|:

    >>> lag(0.0)
    >>> damp(1.0)
    >>> test("hstream_v1_ex2")
    |  date | qjoints | input1 | input2 | output |
    ----------------------------------------------
    | 00:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 01:00 |     1.0 |    0.0 |    1.0 |    1.0 |
    | 02:00 |     6.0 |    1.0 |    5.0 |    6.0 |
    | 03:00 |    12.0 |    3.0 |    9.0 |   12.0 |
    | 04:00 |    10.0 |    2.0 |    8.0 |   10.0 |
    | 05:00 |     6.0 |    1.0 |    5.0 |    6.0 |
    | 06:00 |     3.0 |    0.0 |    3.0 |    3.0 |
    | 07:00 |     2.0 |    0.0 |    2.0 |    2.0 |
    | 08:00 |     1.0 |    0.0 |    1.0 |    1.0 |
    | 09:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 10:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 11:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 12:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 13:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 14:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 15:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 16:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 17:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 18:00 |     0.0 |    0.0 |    0.0 |    0.0 |
    | 19:00 |     0.0 |    0.0 |    0.0 |    0.0 |

    .. raw:: html

        <a
            href="hstream_v1_ex2.html"
            target="_blank"
        >Click here to see the graph</a>

    **Example 3**

    With a lag time of three hours and zero damping, |hstream_v1|
    passes the flow values from one junction to the next one within
    each simulation time step.  Three segments give an overall time
    shift of three hours:

    >>> lag(3.0)
    >>> damp(0.0)
    >>> test("hstream_v1_ex3")
    |  date |                   qjoints | input1 | input2 | output |
    ----------------------------------------------------------------
    | 00:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 01:00 |  1.0   0.0   0.0      0.0 |    0.0 |    1.0 |    0.0 |
    | 02:00 |  6.0   1.0   0.0      0.0 |    1.0 |    5.0 |    0.0 |
    | 03:00 | 12.0   6.0   1.0      0.0 |    3.0 |    9.0 |    0.0 |
    | 04:00 | 10.0  12.0   6.0      1.0 |    2.0 |    8.0 |    1.0 |
    | 05:00 |  6.0  10.0  12.0      6.0 |    1.0 |    5.0 |    6.0 |
    | 06:00 |  3.0   6.0  10.0     12.0 |    0.0 |    3.0 |   12.0 |
    | 07:00 |  2.0   3.0   6.0     10.0 |    0.0 |    2.0 |   10.0 |
    | 08:00 |  1.0   2.0   3.0      6.0 |    0.0 |    1.0 |    6.0 |
    | 09:00 |  0.0   1.0   2.0      3.0 |    0.0 |    0.0 |    3.0 |
    | 10:00 |  0.0   0.0   1.0      2.0 |    0.0 |    0.0 |    2.0 |
    | 11:00 |  0.0   0.0   0.0      1.0 |    0.0 |    0.0 |    1.0 |
    | 12:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 13:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 14:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 15:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 16:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 17:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 18:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |
    | 19:00 |  0.0   0.0   0.0      0.0 |    0.0 |    0.0 |    0.0 |

    .. raw:: html

        <a
            href="hstream_v1_ex3.html"
            target="_blank"
        >Click here to see the graph</a>

    **Example 4**

    The last example shows the highest possible attenuation for three
    river segments:

    >>> lag(3.0)
    >>> damp(1.0)
    >>> test("hstream_v1_ex4")
    |  date |                            qjoints | input1 | input2 |   output |
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

    .. raw:: html

        <a
            href="hstream_v1_ex4.html"
            target="_blank"
        >Click here to see the graph</a>
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import masktools
from hydpy.core import modeltools

# ...from hstream
from hydpy.models.hstream import hstream_masks
from hydpy.models.hstream import hstream_model


class Model(modeltools.AdHocModel):
    """The HBV96 version of HydPy-H-Stream (|hstream_v1|)."""

    INLET_METHODS = (hstream_model.Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (hstream_model.Calc_QJoints_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = (hstream_model.Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()


class Masks(masktools.Masks):
    """Masks applicable to |hstream_v1|."""

    # pylint: disable=no-member
    # bug of pylint 2.4?
    CLASSES = hstream_masks.Masks.CLASSES


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
