# pylint: disable=line-too-long, unused-wildcard-import
"""
|conv_idw_cm| extends |conv_idw| by taking long-term averages at the input and output
nodes into account.  Ratios of the current input values to their long-term averages are
IDW-interpolated to the output nodes, and then multiplied by the long-term averages at
the output nodes.  This approach brings climatological knowledge into the interpolation
results.  Because of the multiplicative adjustment, it suits intermittent variables
that are often zero, like precipitation.

You need to estimate the long-term averages in advance, in whatever way seems
appropriate.  One example is the REGNIE method of the Deutscher Wetterdienst, which
:cite:t:`ref-Rauthe2013` use to generate the HYRAS precipitation data set.  For this
purpose, they preprocess monthly long-term averages using external information such as
elevation.  Their interpolation of daily precipitation values relies on the four
closest stations, weighted with an exponent of two.

You can define the averages in arbitrary units; for example, mm/month and m/year would
be equally fine, as long as you apply them consistently to the input and output
locations.

Integration tests
=================

.. how_to_understand_integration_tests::

We begin by repeating the examples documented for application model |conv_idw|.  We
first define identical test settings (see the documentation on application model
|conv_idw| for more information):

>>> from hydpy import Element, Node, pub
>>> pub.timegrids = "2000-01-01", "2000-01-04", "1d"

>>> from hydpy.models.conv_idw_cm import *
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

If all input and output nodes have the same long-term average, all adjustments cancel
out, and |conv_idw_cm| reproduces the results of the test examples documented for
application model |conv_idw| precisely:

>>> inputaverages(in1=800.0, in2=800.0, in3=800.0)
>>> outputaverages(out1=800.0, out2=800.0, out3=800.0, out4=800.0)
>>> test()
|       date |           inputs |               currentinputaverages |                      currentoutputaverages |                   inputratios |                             outputratios |                 outputs | in1 | in2 | in3 | out1 | out2 | out3 | out4 |
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 800.0  800.0                 800.0 | 800.0  800.0  800.0                  800.0 | 0.00125  0.00375        0.005 | 0.00125  0.00375  0.002188         0.003 | 1.0  3.0  1.75      2.4 | 1.0 | 3.0 | 4.0 |  1.0 |  3.0 | 1.75 |  2.4 |
| 2000-01-02 | nan  2.0     nan | 800.0  800.0                 800.0 | 800.0  800.0  800.0                  800.0 |     nan   0.0025          nan |  0.0025   0.0025    0.0025        0.0025 | 2.0  2.0   2.0      2.0 | nan | 2.0 | nan |  2.0 |  2.0 |  2.0 |  2.0 |
| 2000-01-03 | nan  nan     nan | 800.0  800.0                 800.0 | 800.0  800.0  800.0                  800.0 |     nan      nan          nan |     nan      nan       nan           nan | nan  nan   nan      nan | nan | nan | nan |  nan |  nan |  nan |  nan |

>>> maxnmbinputs(2)
>>> test()
|       date |           inputs |               currentinputaverages |                      currentoutputaverages |                   inputratios |                              outputratios |                          outputs | in1 | in2 | in3 | out1 |     out2 |     out3 | out4 |
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 800.0  800.0                 800.0 | 800.0  800.0  800.0                  800.0 | 0.00125  0.00375        0.005 | 0.00125  0.003882  0.001932        0.0025 | 1.0  3.105263  1.545455      2.0 | 1.0 | 3.0 | 4.0 |  1.0 | 3.105263 | 1.545455 |  2.0 |
| 2000-01-02 | nan  2.0     nan | 800.0  800.0                 800.0 | 800.0  800.0  800.0                  800.0 |     nan   0.0025          nan |     nan    0.0025       nan        0.0025 | nan       2.0       nan      2.0 | nan | 2.0 | nan |  nan |      2.0 |      nan |  2.0 |
| 2000-01-03 | nan  nan     nan | 800.0  800.0                 800.0 | 800.0  800.0  800.0                  800.0 |     nan      nan          nan |     nan       nan       nan           nan | nan       nan       nan      nan | nan | nan | nan |  nan |      nan |      nan |  nan |

Now we define different averages.  Output node `out1` lies at the same location as input
node `in1` and has the same average.  Hence, it receives the original value of `in1`, if
available.  The other output nodes' values reflect their averages:

>>> maxnmbinputs(3)
>>> inputaverages(in1=800.0, in2=1000.0, in3=600.0)
>>> outputaverages(out1=800.0, out2=900.0, out3=700.0, out4=650.0)
>>> test()
|       date |           inputs |                currentinputaverages |                      currentoutputaverages |                 inputratios |                              outputratios |                          outputs | in1 | in2 | in3 | out1 |    out2 |     out3 |     out4 |
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 800.0  1000.0                 600.0 | 800.0  900.0  700.0                  650.0 | 0.00125  0.003     0.006667 | 0.00125  0.003279  0.002342      0.003033 | 1.0  2.95125  1.639714  1.971667 | 1.0 | 3.0 | 4.0 |  1.0 | 2.95125 | 1.639714 | 1.971667 |
| 2000-01-02 | nan  2.0     nan | 800.0  1000.0                 600.0 | 800.0  900.0  700.0                  650.0 |     nan  0.002          nan |   0.002     0.002     0.002         0.002 | 1.6      1.8       1.4       1.3 | nan | 2.0 | nan |  1.6 |     1.8 |      1.4 |      1.3 |
| 2000-01-03 | nan  nan     nan | 800.0  1000.0                 600.0 | 800.0  900.0  700.0                  650.0 |     nan    nan          nan |     nan       nan       nan           nan | nan      nan       nan       nan | nan | nan | nan |  nan |     nan |      nan |      nan |

A different average for `out1` scales the value of `in1` accordingly:

>>> outputaverages(out1=1200.0, out2=900.0, out3=700.0, out4=650.0)
>>> test()
|       date |           inputs |                currentinputaverages |                       currentoutputaverages |                 inputratios |                              outputratios |                          outputs | in1 | in2 | in3 | out1 |    out2 |     out3 |     out4 |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 800.0  1000.0                 600.0 | 1200.0  900.0  700.0                  650.0 | 0.00125  0.003     0.006667 | 0.00125  0.003279  0.002342      0.003033 | 1.5  2.95125  1.639714  1.971667 | 1.0 | 3.0 | 4.0 |  1.5 | 2.95125 | 1.639714 | 1.971667 |
| 2000-01-02 | nan  2.0     nan | 800.0  1000.0                 600.0 | 1200.0  900.0  700.0                  650.0 |     nan  0.002          nan |   0.002     0.002     0.002         0.002 | 2.4      1.8       1.4       1.3 | nan | 2.0 | nan |  2.4 |     1.8 |      1.4 |      1.3 |
| 2000-01-03 | nan  nan     nan | 800.0  1000.0                 600.0 | 1200.0  900.0  700.0                  650.0 |     nan    nan          nan |     nan       nan       nan           nan | nan      nan       nan       nan | nan | nan | nan |  nan |     nan |      nan |      nan |

Only the relationships between the input and output averages matter.  Hence, using
other units (here, daily instead of annual values) changes the ratios but not the final
results:

>>> inputaverages(in1=800.0 / 366.0, in2=1000.0 / 366.0, in3=600.0 / 366.0)
>>> outputaverages(out1=1200.0 / 366.0,
...                out2=900.0 / 366.0,
...                out3=700.0 / 366.0,
...                out4=650.0 / 366.0)
>>> test()
|       date |           inputs |                    currentinputaverages |                               currentoutputaverages |                inputratios |                             outputratios |                          outputs | in1 | in2 | in3 | out1 |    out2 |     out3 |     out4 |
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 2.185792  2.73224              1.639344 | 3.278689  2.459016  1.912568               1.775956 | 0.4575  1.098         2.44 | 0.4575  1.200175  0.857336        1.1102 | 1.5  2.95125  1.639714  1.971667 | 1.0 | 3.0 | 4.0 |  1.5 | 2.95125 | 1.639714 | 1.971667 |
| 2000-01-02 | nan  2.0     nan | 2.185792  2.73224              1.639344 | 3.278689  2.459016  1.912568               1.775956 |    nan  0.732          nan |  0.732     0.732     0.732         0.732 | 2.4      1.8       1.4       1.3 | nan | 2.0 | nan |  2.4 |     1.8 |      1.4 |      1.3 |
| 2000-01-03 | nan  nan     nan | 2.185792  2.73224              1.639344 | 3.278689  2.459016  1.912568               1.775956 |    nan    nan          nan |    nan       nan       nan           nan | nan      nan       nan       nan | nan | nan | nan |  nan |     nan |      nan |      nan |

Stations with zero averages do not contribute to the interpolation (see station `in2`).
Target points with zero averages receive zero values (see node `out2`):

>>> inputaverages(in1=800.0, in2=0.0, in3=600.0)
>>> outputaverages(out1=800.0, out2=0.0, out3=700.0, out4=650.0)
>>> test()
|       date |           inputs |             currentinputaverages |                    currentoutputaverages |               inputratios |                              outputratios |                      outputs | in1 | in2 | in3 | out1 | out2 |     out3 |     out4 |
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 800.0  0.0                 600.0 | 800.0  0.0  700.0                  650.0 | 0.00125  nan     0.006667 | 0.00125  0.004861  0.002235      0.003056 | 1.0  0.0  1.564394  1.986111 | 1.0 | 3.0 | 4.0 |  1.0 |  0.0 | 1.564394 | 1.986111 |
| 2000-01-02 | nan  2.0     nan | 800.0  0.0                 600.0 | 800.0  0.0  700.0                  650.0 |     nan  nan          nan |     nan       nan       nan           nan | nan  nan       nan       nan | nan | 2.0 | nan |  nan |  nan |      nan |      nan |
| 2000-01-03 | nan  nan     nan | 800.0  0.0                 600.0 | 800.0  0.0  700.0                  650.0 |     nan  nan          nan |     nan       nan       nan           nan | nan  nan       nan       nan | nan | nan | nan |  nan |  nan |      nan |      nan |

Stations with zero averages still count as one of the |MaxNmbInputs| nearest stations
and are not replaced by more distant ones.  If we only consider the nearest station,
`out2` receives |numpy.nan| values, despite its zero average, because station `in2` is
its nearest station:

>>> maxnmbinputs(1)
>>> test()
|       date |           inputs |             currentinputaverages |                    currentoutputaverages |               inputratios |                        outputratios |                  outputs | in1 | in2 | in3 | out1 | out2 |  out3 |   out4 |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-01 | 1.0  3.0     4.0 | 800.0  0.0                 600.0 | 800.0  0.0  700.0                  650.0 | 0.00125  nan     0.006667 | 0.00125  nan  0.00125       0.00125 | 1.0  nan  0.875   0.8125 | 1.0 | 3.0 | 4.0 |  1.0 |  nan | 0.875 | 0.8125 |
| 2000-01-02 | nan  2.0     nan | 800.0  0.0                 600.0 | 800.0  0.0  700.0                  650.0 |     nan  nan          nan |     nan  nan      nan           nan | nan  nan    nan      nan | nan | 2.0 | nan |  nan |  nan |   nan |    nan |
| 2000-01-03 | nan  nan     nan | 800.0  0.0                 600.0 | 800.0  0.0  700.0                  650.0 |     nan  nan          nan |     nan  nan      nan           nan | nan  nan    nan      nan | nan | nan | nan |  nan |  nan |   nan |    nan |

Finally, we demonstrate the application of monthly averages.  We shift the simulation
period to the January-February transition and define averages for two nodes that differ
between the months.  The results change from the second to the third simulation step,
even though the input values stay the same:

>>> pub.timegrids = "2000-01-30", "2000-02-02", "1d"
>>> element.prepare_allseries()
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%m-%d"
>>> inputaverages(in1=[80.0, 40.0, 80.0, 80.0, 80.0, 80.0,
...                    80.0, 80.0, 80.0, 80.0, 80.0, 80.0],
...               in2=100.0,
...               in3=60.0)
>>> outputaverages(out1=80.0,
...                out2=90.0,
...                out3=[70.0, 140.0, 70.0, 70.0, 70.0, 70.0,
...                      70.0, 70.0, 70.0, 70.0, 70.0, 70.0],
...                out4=65.0)
>>> in1.sequences.sim.series = 2.0, 2.0, 2.0
>>> in2.sequences.sim.series = 3.0, 3.0, 3.0
>>> in3.sequences.sim.series = 4.0, 4.0, 4.0
>>> test()
|       date |           inputs |              currentinputaverages |                    currentoutputaverages |              inputratios |                     outputratios |                 outputs | in1 | in2 | in3 | out1 | out2 | out3 |  out4 |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| 2000-01-30 | 2.0  3.0     4.0 | 80.0  100.0                  60.0 | 80.0  90.0   70.0                   65.0 | 0.025  0.03     0.066667 | 0.025  0.03  0.025         0.025 | 2.0  2.7  1.75    1.625 | 2.0 | 3.0 | 4.0 |  2.0 |  2.7 | 1.75 | 1.625 |
| 2000-01-31 | 2.0  3.0     4.0 | 80.0  100.0                  60.0 | 80.0  90.0   70.0                   65.0 | 0.025  0.03     0.066667 | 0.025  0.03  0.025         0.025 | 2.0  2.7  1.75    1.625 | 2.0 | 3.0 | 4.0 |  2.0 |  2.7 | 1.75 | 1.625 |
| 2000-02-01 | 2.0  3.0     4.0 | 40.0  100.0                  60.0 | 80.0  90.0  140.0                   65.0 |  0.05  0.03     0.066667 |  0.05  0.03   0.05          0.05 | 4.0  2.7   7.0     3.25 | 2.0 | 3.0 | 4.0 |  4.0 |  2.7 |  7.0 |  3.25 |
"""

from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.models.conv import conv_model


class Model(conv_model.BaseModel):
    """|conv_idw_cm.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Conv-IDW-CM",
        description="inverse distance weighted interpolation with multiplicative "
        "climatological adjustment",
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (conv_model.Pick_Inputs_V1,)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (conv_model.Interpolate_InverseDistance_V1,)
    RUN_METHODS = (
        conv_model.Calc_CurrentInputAverages_V1,
        conv_model.Calc_CurrentOutputAverages_V1,
        conv_model.Calc_InputRatios_V1,
        conv_model.Calc_OutputRatios_V1,
        conv_model.Calc_Outputs_V4,
    )
    OUTLET_METHODS = (conv_model.Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
