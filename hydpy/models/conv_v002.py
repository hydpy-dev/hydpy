# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Inverse distance weighted interpolation.

Version 2 of HydPy-C performs simple inverse distance weighted interpolations
between an arbitrary number of models (or data files) providing output and an
arbitrary number of models requiring input.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following examples over a simulation period of 3 days:

>>> from hydpy import Element, Node, pub
>>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

|conv_v002| implements no parameter with values depending on the simulation
step size, which is why we can pass anything (or nothing) to function
|parameterstep| without changing the following results:

>>> from hydpy.models.conv_v002 import *
>>> parameterstep()

Due to the following configuration, |conv_v002| queries its input from the
inlet nodes `in1`, `in2`, and `in3` and passes the interpolation results to
the outlet nodes `out1`, `out2`, `out3`, and `out4`:

>>> in1, in2, in3 = Node("in1"), Node("in2"), Node("in3")
>>> element = Element("conv",
...                   inlets=(in1, in2, in3),
...                   outlets=["out1", "out2", "out3", "out4"])

The following coordinate definitions contain the particular case of outlet
node `out1`, being at the same location as inlet node `in1`:

>>> inputcoordinates(
...     in1=(0.0, 3.0),
...     in2=(2.0, -1.0),
...     in3=(4.0, 2.0))
>>> outputcoordinates(
...     out1=(0.0, 3.0),
...     out2=(3.0, -2.0),
...     out3=(1.0, 2.0),
...     out4=(1.0, 1.0))

We set the power parameter |Power| to the standard value of two:

>>> power(2.0)

In the first example, we perform a complete inverse distance weighted
interpolation, where we take all input location into account, as long
as they provide input data:

>>> maxnmbinputs(3)

|conv_v002| does not implement any state or log sequences and thus has
no memory at all, making finalising the test setup quite easy.  We only
need to define time series for both inlet nodes.  Note that we set some
|numpy| |numpy.nan| values to demonstrate how |conv_v002| deals with
missing values:

>>> element.model = model
>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%m-%d"
>>> with pub.options.checkseries(False):
...     in1.sequences.sim.series = 1.0, nan, nan
...     in2.sequences.sim.series = 3.0, 2.0, nan
...     in3.sequences.sim.series = 4.0, nan, nan

If available, outlet node `in1` receives its value from inlet node `in1`
due to the same location.  At the second time step, all outlet nodes
receive the same data as only inlet node `in2` provides any data.  When
no inlet node provides data, the outlet nodes receive |numpy.nan| values:

>>> test()
|       date |           inputs |                 outputs | in1 | in2 | in3 | out1 | out2 | out3 | out4 |
---------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 1.0  3.0  1.75      2.4 | 1.0 | 3.0 | 4.0 |  1.0 |  3.0 | 1.75 |  2.4 |
| 2000-01-02 | nan  2.0     nan | 2.0  2.0   2.0      2.0 | nan | 2.0 | nan |  2.0 |  2.0 |  2.0 |  2.0 |
| 2000-01-03 | nan  nan     nan | nan  nan   nan      nan | nan | nan | nan |  nan |  nan |  nan |  nan |

We can restrict the number of considered inlet nodes via parameter
|MaxNmbInputs|, which can increase computation speed.  However, do not
set to low values. Otherwise, you might deteriorate accuracy severely or
run into the risk of unhandled |numpy.nan| values:

>>> maxnmbinputs(2)
>>> test()
|       date |           inputs |                          outputs | in1 | in2 | in3 | out1 |     out2 |     out3 | out4 |
--------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 1.0  3.105263  1.545455      2.0 | 1.0 | 3.0 | 4.0 |  1.0 | 3.105263 | 1.545455 |  2.0 |
| 2000-01-02 | nan  2.0     nan | nan       2.0       nan      2.0 | nan | 2.0 | nan |  nan |      2.0 |      nan |  2.0 |
| 2000-01-03 | nan  nan     nan | nan       nan       nan      nan | nan | nan | nan |  nan |      nan |      nan |  nan |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.conv import conv_model


class Model(conv_model.BaseModel):
    """Version 2 of the Conv model."""

    INLET_METHODS = (conv_model.Pick_Inputs_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (conv_model.Calc_Outputs_V2,)
    ADD_METHODS = (conv_model.Interpolate_InverseDistance_V1,)
    OUTLET_METHODS = (conv_model.Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
