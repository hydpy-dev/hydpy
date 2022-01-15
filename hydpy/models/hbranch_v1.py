# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""
Version 1 of the HydPy-H-Branch model allows branching the summed input from some inlet
nodes to an arbitrary number of outlet nodes. The original HBV96 implementation
supposes to separate inflowing discharge, but |hbranch_v1| is suitable for separating
arbitrary variables. Calculations are performed for each branch individually by linear
interpolation (or extrapolation) following tabulated supporting points.  Additionally,
|hbranch_v1| allows adjusting the input data with differences that can vary monthly.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 11 hours:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "01.01.2000 00:00", "01.01.2000 11:00", "1h"

|hbranch_v1| has no parameter with values depending on the simulation step size,
which is why we can pass anything (or nothing) to function |parameterstep| without
changing the following results:

>>> from hydpy.models.hbranch_v1 import *
>>> parameterstep()

The |hbranch_v1| model queries inflow from two inlet |Node| objects and passes the
branched outflow to three outlet |Node| objects.  Thus, In contrast to most other
application models, we need to define the parameter values before connecting the
model to its |Element| object, called `branch`:

>>> nodes = Nodes("input1", "input2", "output1", "output2", "output3")
>>> branch = Element("branch",
...                  inlets=["input1", "input2"],
...                  outlets=["output1", "output2", "output3"])
>>> delta(-1.0)
>>> minimum(-1.0)
>>> xpoints(0.0, 2.0, 4.0, 6.0)
>>> ypoints(output1=[0.0, 1.0, 2.0, 3.0],
...         output2=[0.0, 1.0, 0.0, 0.0],
...         output3=[0.0, 0.0, 2.0, 6.0])
>>> branch.model = model

We do not have to define any initial values in the test settings because the
|hbranch_v1| has no memory:

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(branch)
>>> test.dateformat = "%H:%M"

The (identical) values of the inlet nodes `input1` and `input2` define no realistic
inflow series.  Instead, they serve to show the behaviour of |hbranch_v1| within and
outside the current range defined by parameter |XPoints|:

>>> import numpy
>>> nodes.input1.sequences.sim.series = numpy.arange(-1.0, 10.0)/2
>>> nodes.input2.sequences.sim.series = numpy.arange(-1.0, 10.0)/2

`output1` shows linear continuations below and above the current range of parameter
|XPoints|. `output2` points out that inverse relationships are allowed. `output3` shows
that |hbranch_v1| does not enforce equality between the total sum of input and output
values:

.. integration-test::

    >>> test("hbranch_v1_ex1")
    |  date | originalinput | adjustedinput |             outputs | input1 | input2 | output1 | output2 | output3 |
    ---------------------------------------------------------------------------------------------------------------
    | 00:00 |          -1.0 |          -1.0 | -0.5  -0.5      0.0 |   -0.5 |   -0.5 |    -0.5 |    -0.5 |     0.0 |
    | 01:00 |           0.0 |          -1.0 | -0.5  -0.5      0.0 |    0.0 |    0.0 |    -0.5 |    -0.5 |     0.0 |
    | 02:00 |           1.0 |           0.0 |  0.0   0.0      0.0 |    0.5 |    0.5 |     0.0 |     0.0 |     0.0 |
    | 03:00 |           2.0 |           1.0 |  0.5   0.5      0.0 |    1.0 |    1.0 |     0.5 |     0.5 |     0.0 |
    | 04:00 |           3.0 |           2.0 |  1.0   1.0      0.0 |    1.5 |    1.5 |     1.0 |     1.0 |     0.0 |
    | 05:00 |           4.0 |           3.0 |  1.5   0.5      1.0 |    2.0 |    2.0 |     1.5 |     0.5 |     1.0 |
    | 06:00 |           5.0 |           4.0 |  2.0   0.0      2.0 |    2.5 |    2.5 |     2.0 |     0.0 |     2.0 |
    | 07:00 |           6.0 |           5.0 |  2.5   0.0      4.0 |    3.0 |    3.0 |     2.5 |     0.0 |     4.0 |
    | 08:00 |           7.0 |           6.0 |  3.0   0.0      6.0 |    3.5 |    3.5 |     3.0 |     0.0 |     6.0 |
    | 09:00 |           8.0 |           7.0 |  3.5   0.0      8.0 |    4.0 |    4.0 |     3.5 |     0.0 |     8.0 |
    | 10:00 |           9.0 |           8.0 |  4.0   0.0     10.0 |    4.5 |    4.5 |     4.0 |     0.0 |    10.0 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from hbranch
from hydpy.models.hbranch import hbranch_model


class Model(hbranch_model.Model):
    """The HBV96 version of HydPy-H-Stream (hbranch_v1)."""

    INLET_METHODS = (hbranch_model.Pick_OriginalInput_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        hbranch_model.Calc_AdjustedInput_V1,
        hbranch_model.Calc_Outputs_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (hbranch_model.Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
