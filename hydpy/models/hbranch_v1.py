# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""
Version 1 of the HydPy-H-Branch model allows for branching the
summed input from some inlet nodes to an arbitrary number of outlet
nodes.  In the original HBV96 implementation, it is supposed to
separate inflowing discharge, but in *HydPy* it can be used for
arbitrary variables.  Calculations are performed for each branch
individually by linear interpolation (or extrapolation) following
tabulated supporting points.

Integration tests
=================

    .. how_to_understand_integration_tests::

    We perform the following examples over a simulation period of 10 hours:

    >>> from hydpy import pub, Nodes, Element
    >>> pub.timegrids = "01.01.2000 00:00", "01.01.2000 10:00", "1h"

    |hbranch_v1| has no parameter with values depending on the simulation
    step size, which is why we can pass anything (or nothing) to function
    |parameterstep| without changing the following results:

    >>> from hydpy.models.hbranch_v1 import *
    >>> parameterstep()

    The |hbranch_v1| model queries its inflow from two inlet |Node| objects
    and passes the branched outflow to three outlet |Node| objects.  In
    contrast to most other application models, we need to define the
    parameter values before connecting the model to its |Element| object,
    called `branch`:

    >>> nodes = Nodes("input1", "input2", "output1", "output2", "output3")
    >>> branch = Element("branch",
    ...                  inlets=["input1", "input2"],
    ...                  outlets=["output1", "output2", "output3"])
    >>> xpoints(0.0, 2.0, 4.0, 6.0)
    >>> ypoints(output1=[0.0, 1.0, 2.0, 3.0],
    ...         output2=[0.0, 1.0, 0.0, 0.0],
    ...         output3=[0.0, 0.0, 2.0, 6.0])
    >>> branch.model = model

    We do not have to define any initial values in the test settings,
    due to application model |hbranch_v1| having no memory at all:

    >>> from hydpy.core.testtools import IntegrationTest
    >>> test = IntegrationTest(branch)
    >>> test.dateformat = "%H:%M"

    The (identical) values of the inlet nodes `input1` and `input2`
    define no realistic inflow series.  Instead, they are just
    intended to show the behaviour of |hbranch_v1| within and slightly
    outside the current range defined by parameter |XPoints|:

    >>> import numpy
    >>> nodes.input1.sequences.sim.series = numpy.arange(-1, 9)/2
    >>> nodes.input2.sequences.sim.series = numpy.arange(-1, 9)/2

    The results for outlet node `output1` clearly show that the linear
    interpolation is extrapolated both below and above the current range
    of parameter |XPoints|.  The values of node `output2` point out that
    inverse relationships are allowed.  The values of node `output3`
    raise to fast for high input values, showing that |hbranch_v1| does
    not care for equality between the total sum of input and output values:

    >>> test("hbranch_v1_ex1")
    |  date | input |             outputs | input1 | input2 | output1 | output2 | output3 |
    ---------------------------------------------------------------------------------------
    | 00:00 |  -1.0 | -0.5  -0.5      0.0 |   -0.5 |   -0.5 |    -0.5 |    -0.5 |     0.0 |
    | 01:00 |   0.0 |  0.0   0.0      0.0 |    0.0 |    0.0 |     0.0 |     0.0 |     0.0 |
    | 02:00 |   1.0 |  0.5   0.5      0.0 |    0.5 |    0.5 |     0.5 |     0.5 |     0.0 |
    | 03:00 |   2.0 |  1.0   1.0      0.0 |    1.0 |    1.0 |     1.0 |     1.0 |     0.0 |
    | 04:00 |   3.0 |  1.5   0.5      1.0 |    1.5 |    1.5 |     1.5 |     0.5 |     1.0 |
    | 05:00 |   4.0 |  2.0   0.0      2.0 |    2.0 |    2.0 |     2.0 |     0.0 |     2.0 |
    | 06:00 |   5.0 |  2.5   0.0      4.0 |    2.5 |    2.5 |     2.5 |     0.0 |     4.0 |
    | 07:00 |   6.0 |  3.0   0.0      6.0 |    3.0 |    3.0 |     3.0 |     0.0 |     6.0 |
    | 08:00 |   7.0 |  3.5   0.0      8.0 |    3.5 |    3.5 |     3.5 |     0.0 |     8.0 |
    | 09:00 |   8.0 |  4.0   0.0     10.0 |    4.0 |    4.0 |     4.0 |     0.0 |    10.0 |

    .. raw:: html

        <a
            href="hbranch_v1_ex1.html"
            target="_blank"
        >Click here to see the graph</a>
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from hbranch
from hydpy.models.hbranch import hbranch_model


class Model(hbranch_model.Model):
    """The HBV96 version of HydPy-H-Stream (hbranch_v1)."""

    INLET_METHODS = (hbranch_model.Pick_Input_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (hbranch_model.Calc_Outputs_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = (hbranch_model.Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
