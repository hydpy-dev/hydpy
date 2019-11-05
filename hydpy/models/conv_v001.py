# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Nearest-neighbour interpolation.

Version 1 of HydPy-C performs simple nearest-neighbour interpolations between
an arbitrary number of models (or data files) providing output and an arbitrary
number of models requiring input.

Integration test:

We perform the following examples over a simulation period of 3 days:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = '2000-01-01', '2000-01-04', '1d'

|conv_v001| provides no parameter with values depending on the simulation
step size, which is why we can pass anything (or nothing) to function
|parameterstep| without changing the following results:

>>> from hydpy.models.conv_v001 import *
>>> parameterstep()

Due to the following configuration, |conv_v001| queries its input from the
inlet nodes `in1` and `in2` and passes the interpolation results to the
oulet nodes `out1`, `out2`, `out3`, and `out4`:

>>> from hydpy import *
>>> in1, in2 = Node('in1'), Node('in2')
>>> element = Element('conv',
...                   inlets=(in1, in2),
...                   outlets=['out1', 'out2', 'out3', 'out4'])

The following coordinate definitions contain the special case of outlet
node `out4`, being in the middle of inlet nodes `in1` and `in2` exactly:

>>> inputcoordinates(
...     in1=(0.0, 3.0),
...     in2=(2.0, -1.0))
>>> outputcoordinates(
...     out1=(0.0, 3.0),
...     out2=(3.0, -2.0),
...     out3=(1.0, 2.0),
...     out4=(1.0, 1.0))

|conv_v001| does not implement any state or log sequences and thus has
no memory at all, making finalising the test setup quite easy.  We only
need to define time series for both inlet nodes:

>>> element.model = model
>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = '%Y-%m-%d'
>>> in1.sequences.sim.series = 1.0, 2.0, 3.0
>>> in2.sequences.sim.series = 4.0, 5.0, 6.0

The calculated results provides no supprises.  However, note that outlet
node `out4` received the output of node `in1` instead of the equidistantly
node `in2`, which is due to their definition order when preparing parameter
|InputCoordinates| above:

>>> test()
|       date |      inputs |                outputs | in1 | in2 | out1 | out2 | out3 | out4 |
---------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0     4.0 | 1.0  4.0  1.0      1.0 | 1.0 | 4.0 |  1.0 |  4.0 |  1.0 |  1.0 |
| 2000-01-02 | 2.0     5.0 | 2.0  5.0  2.0      2.0 | 2.0 | 5.0 |  2.0 |  5.0 |  2.0 |  2.0 |
| 2000-01-03 | 3.0     6.0 | 3.0  6.0  3.0      3.0 | 3.0 | 6.0 |  3.0 |  6.0 |  3.0 |  3.0 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.conv import conv_model


class Model(conv_model.Model):
    """Version 1 of the Conv model."""
    INLET_METHODS = (
        conv_model.Pick_Inputs_V1,
    )
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        conv_model.Calc_Outputs_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (
        conv_model.Pass_Outputs_V1,
    )
    SENDER_METHODS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
