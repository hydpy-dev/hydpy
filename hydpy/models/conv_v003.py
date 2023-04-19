# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Inverse distance weighted interpolation with external drift.

Version 3 of HydPy-C extends version 2 by taking an additional
statistical relationship between the interpolated variable and an arbitrary
independent variable into account.  A typical use case is elevation-dependent
temperature interpolation.  You can understand the approach of |conv_v003|
as a simplification of External Drift Kriging.

The algorithm works as follows (we take elevation-dependent temperature
interpolation as an example):

 * Estimate the linear regression coefficients to model the relationship
   between air temperature and elevation at the available stations for the
   current simulation time step (or take the given default values).
 * Use the resulting linear model to predict the temperature at the stations
   and the interpolation target points.
 * Calculate the residuals (differences between predictions and measurements)
   at all stations.
 * Interpolate the residuals based on the same inverse distance weighting
   approach as applied by application model |conv_v002|.
 * Combine the predicted temperature values and the interpolated residuals
   to gain the final interpolation results at all target points.

For perfect correlations between temperature and elevation, the interpolated
values depend only on elevation.  If there is no correlation, the interpolated
values depend solely on spatial proximity to the stations.

Integration tests
=================

.. how_to_understand_integration_tests::

We start the following explanations with repeating the examples documented for
application model |conv_v002|.  Hence, we first define identical test settings
(please see the documentation on application model |conv_v002| for more information):


>>> from hydpy import Element, Node, pub
>>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

>>> from hydpy.models.conv_v003 import *
>>> parameterstep()

>>> in1, in2, in3 = Node("in1"), Node("in2"), Node("in3")
>>> element = Element("conv",
...                   inlets=(in1, in2, in3),
...                   outlets=["out1", "out2", "out3", "out4"])

>>> inputcoordinates(in1=(0.0, 3.0),
...                  in2=(2.0, -1.0),
...                  in3=(4.0, 2.0))
>>> outputcoordinates(out1=(0.0, 3.0),
...                   out2=(3.0, -2.0),
...                   out3=(1.0, 2.0),
...                   out4=(1.0, 1.0))
>>> power(2.0)
>>> maxnmbinputs(3)

>>> element.model = model
>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%m-%d"
>>> with pub.options.checkseries(False):
...     in1.sequences.sim.series = 1.0, nan, nan
...     in2.sequences.sim.series = 3.0, 2.0, nan
...     in3.sequences.sim.series = 4.0, nan, nan

Next, we prepare the additional parameters of |conv_v003|.  Most importantly, we
define the values of the independent variable for all input and output nodes:

>>> inputheights(in1=0.0,
...              in2=2.0,
...              in3=4.0)
>>> outputheights(out1=0.0,
...               out2=1.0,
...               out3=2.0,
...               out4=3.0)

In our example calculations, we use three input nodes.  However, we first set the
number of data-points that must be available to estimate the linear model to four,
which of course is impossible.  Hence, |conv_v003| will always use the default values.
We set both of them to zero and thus effectively disable the "external drift"
functionality so that |conv_v003| works exactly like |conv_v002|:

>>> minnmbinputs(4)
>>> defaultconstant(0.0)
>>> defaultfactor(0.0)

Under the given configuration, |conv_v003| reproduces the results of the test
examples documented for application model |conv_v002| precisely:

>>> test()
|       date |           inputs | actualconstant | actualfactor |           inputpredictions |                outputpredictions |           inputresiduals |                 outputresiduals |                 outputs | in1 | in2 | in3 | out1 | out2 | out3 | out4 |
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 |            0.0 |          0.0 | 0.0  0.0               0.0 | 0.0  0.0  0.0                0.0 | 1.0  3.0             4.0 | 1.0  3.0  1.75              2.4 | 1.0  3.0  1.75      2.4 | 1.0 | 3.0 | 4.0 |  1.0 |  3.0 | 1.75 |  2.4 |
| 2000-01-02 | nan  2.0     nan |            0.0 |          0.0 | 0.0  0.0               0.0 | 0.0  0.0  0.0                0.0 | nan  2.0             nan | 2.0  2.0   2.0              2.0 | 2.0  2.0   2.0      2.0 | nan | 2.0 | nan |  2.0 |  2.0 |  2.0 |  2.0 |
| 2000-01-03 | nan  nan     nan |            0.0 |          0.0 | 0.0  0.0               0.0 | 0.0  0.0  0.0                0.0 | nan  nan             nan | nan  nan   nan              nan | nan  nan   nan      nan | nan | nan | nan |  nan |  nan |  nan |  nan |

>>> maxnmbinputs(2)
>>> test()
|       date |           inputs | actualconstant | actualfactor |           inputpredictions |                outputpredictions |           inputresiduals |                          outputresiduals |                          outputs | in1 | in2 | in3 | out1 |     out2 |     out3 | out4 |
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 |            0.0 |          0.0 | 0.0  0.0               0.0 | 0.0  0.0  0.0                0.0 | 1.0  3.0             4.0 | 1.0  3.105263  1.545455              2.0 | 1.0  3.105263  1.545455      2.0 | 1.0 | 3.0 | 4.0 |  1.0 | 3.105263 | 1.545455 |  2.0 |
| 2000-01-02 | nan  2.0     nan |            0.0 |          0.0 | 0.0  0.0               0.0 | 0.0  0.0  0.0                0.0 | nan  2.0             nan | nan       2.0       nan              2.0 | nan       2.0       nan      2.0 | nan | 2.0 | nan |  nan |      2.0 |      nan |  2.0 |
| 2000-01-03 | nan  nan     nan |            0.0 |          0.0 | 0.0  0.0               0.0 | 0.0  0.0  0.0                0.0 | nan  nan             nan | nan       nan       nan              nan | nan       nan       nan      nan | nan | nan | nan |  nan |      nan |      nan |  nan |

Now we enable the "external drift" functionality by providing non-zero default values.
Hence, |conv_v003| employs the same linear model in all simulation time steps:

>>> maxnmbinputs(3)
>>> defaultfactor(1.0)
>>> defaultconstant(2.0)
>>> test()
|       date |           inputs | actualconstant | actualfactor |           inputpredictions |                outputpredictions |             inputresiduals |                       outputresiduals |                    outputs | in1 | in2 | in3 | out1 | out2 |    out3 | out4 |
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 |            2.0 |          1.0 | 2.0  4.0               6.0 | 2.0  3.0  4.0                5.0 | -1.0  -1.0            -2.0 | -1.0  -1.1  -1.15625             -1.2 | 1.0  1.9  2.84375      3.8 | 1.0 | 3.0 | 4.0 |  1.0 |  1.9 | 2.84375 |  3.8 |
| 2000-01-02 | nan  2.0     nan |            2.0 |          1.0 | 2.0  4.0               6.0 | 2.0  3.0  4.0                5.0 |  nan  -2.0             nan | -2.0  -2.0      -2.0             -2.0 | 0.0  1.0      2.0      3.0 | nan | 2.0 | nan |  0.0 |  1.0 |     2.0 |  3.0 |
| 2000-01-03 | nan  nan     nan |            2.0 |          1.0 | 2.0  4.0               6.0 | 2.0  3.0  4.0                5.0 |  nan   nan             nan |  nan   nan       nan              nan | nan  nan      nan      nan | nan | nan | nan |  nan |  nan |     nan |  nan |

If we set the required number of data-points to three (two would also be fine),
|conv_v003| estimates the parameters of the linear model (|ActualFactor| and
|ActualConstant|) in the first time step on its own, and falls back to the
default values in the remaining time steps:

>>> minnmbinputs(2)
>>> test()
|       date |           inputs | actualconstant | actualfactor |                     inputpredictions |                               outputpredictions |                      inputresiduals |                                 outputresiduals |                       outputs | in1 | in2 | in3 | out1 |  out2 |     out3 | out4 |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 |       1.166667 |         0.75 | 1.166667  2.666667          4.166667 | 1.166667  1.916667  2.666667           3.416667 | -0.166667  0.333333       -0.166667 | -0.166667  0.258333  -0.096354         0.033333 | 1.0  2.175  2.570312     3.45 | 1.0 | 3.0 | 4.0 |  1.0 | 2.175 | 2.570312 | 3.45 |
| 2000-01-02 | nan  2.0     nan |            2.0 |          1.0 |      2.0       4.0               6.0 |      2.0       3.0       4.0                5.0 |       nan      -2.0             nan |      -2.0      -2.0       -2.0             -2.0 | 0.0    1.0       2.0      3.0 | nan | 2.0 | nan |  0.0 |   1.0 |      2.0 |  3.0 |
| 2000-01-03 | nan  nan     nan |            2.0 |          1.0 |      2.0       4.0               6.0 |      2.0       3.0       4.0                5.0 |       nan       nan             nan |       nan       nan        nan              nan | nan    nan       nan      nan | nan | nan | nan |  nan |   nan |      nan |  nan |

The final example shows that everything works as expected for the edge cases of
perfect and missing correlation. In the first time step, there is a perfect
(negative) correlation at the input nodes.  Hence, all residuals (calculated for
the input nodes and interpolated for the output nodes) are zero.  In the second
time step, there is no correlation.  Hence, all values predicted by the linear
model are the same.  The third time step shows that |conv_v003| handles the
special (but not uncommon) case of missing variability in the input values well:

>>> in1.sequences.sim.series = 4.0, 0.0, 0.0
>>> in2.sequences.sim.series = 3.0, 1.0, 0.0
>>> in3.sequences.sim.series = 2.0, 0.0, 0.0
>>> test()
|       date |           inputs | actualconstant | actualfactor |                     inputpredictions |                               outputpredictions |                      inputresiduals |                                 outputresiduals |                      outputs | in1 | in2 | in3 | out1 | out2 |     out3 | out4 |
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 4.0  3.0     2.0 |            4.0 |         -0.5 |      4.0       3.0               2.0 |      4.0       3.5       3.0                2.5 |       0.0       0.0             0.0 |       0.0       0.0        0.0              0.0 | 4.0   3.5       3.0      2.5 | 4.0 | 3.0 | 2.0 |  4.0 |  3.5 |      3.0 |  2.5 |
| 2000-01-02 | 0.0  1.0     0.0 |       0.333333 |          0.0 | 0.333333  0.333333          0.333333 | 0.333333  0.333333  0.333333           0.333333 | -0.333333  0.666667       -0.333333 | -0.333333  0.516667  -0.192708         0.066667 | 0.0  0.85  0.140625      0.4 | 0.0 | 1.0 | 0.0 |  0.0 | 0.85 | 0.140625 |  0.4 |
| 2000-01-03 | 0.0  0.0     0.0 |            0.0 |          0.0 |      0.0       0.0               0.0 |      0.0       0.0       0.0                0.0 |       0.0       0.0             0.0 |       0.0       0.0        0.0              0.0 | 0.0   0.0       0.0      0.0 | 0.0 | 0.0 | 0.0 |  0.0 |  0.0 |      0.0 |  0.0 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.conv import conv_model


class Model(conv_model.BaseModel):
    """Version 3 of the Conv model."""

    INLET_METHODS = (conv_model.Pick_Inputs_V1,)
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        conv_model.Return_Mean_V1,
        conv_model.Interpolate_InverseDistance_V1,
    )
    RUN_METHODS = (
        conv_model.Calc_ActualConstant_ActualFactor_V1,
        conv_model.Calc_InputPredictions_V1,
        conv_model.Calc_OutputPredictions_V1,
        conv_model.Calc_InputResiduals_V1,
        conv_model.Calc_OutputResiduals_V1,
        conv_model.Calc_Outputs_V3,
    )
    OUTLET_METHODS = (conv_model.Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
