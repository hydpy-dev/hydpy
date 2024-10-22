"""
|arma_rimorido| relies on the RIMO/RIDO method, which is based on the `translation
diffusion equation`, which is a linear approximation of the Saint-Venant equations
involving only two parameters - one for the celerity and one for the diffusivity of the
flood wave.  The linearity of the approach allows for constructing Unit Hydrograph
ordinates for each specific combination of celerity, diffusivity, and the length of the
considered river section.  One can understand these ordinates as coefficients of a
moving average (MA) process.

|arma_rimorido| adds two additional features to this conventional approach.

Firstly, RIMO/RIDO approximates the response function described by the MA coefficients
by an ARMA process, which is helpful for response functions with long tails.  Very
often, autoregressive (AR) modelscan approximate long-tailed responses sufficiently
with few parameters.  Hence, ARMA models (which reflect the rising limb of a response
function with their MA coefficients and its falling limb with their AR coefficients)
are often more parameter efficient than pure MA models.

Secondly, RIMO/RIDO separates the flow into the river section into different "portions"
based on discharge thresholds.  Each portion is routed by a separate ARMA model,
allowing RIMO/RIDO to reflect the nonlinearity of rating curves to a certain degree.
For example, the bank-full discharge can serve as a threshold.  Then, one can apply
smaller celerity values and larger diffusivity values on the "upper" flow portion to
simulate retention processes on floodplains.

If you want to apply |arma_rimorido| precisely like RIMO/RIDO, consider using
|TranslationDiffusionEquation| for calculating its coefficients.  But you can also
define them differently, e.g. using |LinearStorageCascade|. Additionally, you are free
to apply combined ARMA coefficients or pure MA coefficients only, as described in the
following examples.

Integration tests
=================

.. how_to_understand_integration_tests::

We perform the following tests over 20 hours:

>>> from hydpy import pub, Nodes, Element
>>> pub.timegrids = "01.01.2000 00:00",  "01.01.2000 20:00", "1h"

Import the model and define the time settings:

>>> from hydpy.models.arma_rimorido import *
>>> parameterstep("1h")

For testing purposes, |arma_rimorido| shall retrieve its input from the nodes `input1`
and `input2` and pass its output to the node `output`.  Firstly, we define all nodes:

>>> nodes = Nodes("input1", "input2", "output")

Define the element `stream` and build the connections between the nodes defined above
and the |arma_rimorido| model instance:

>>> stream = Element("stream",
...                  inlets=["input1", "input2"],
...                  outlets="output")
>>> stream.model = model

Prepare a test function object, which prints the respective values of the model
sequences |QIn|, |QPIn|, |QPOut|, and |QOut|.  The node sequence `sim` is added in
to that the values calculated for |QOut| are actually passed to `sim`:

>>> from hydpy import IntegrationTest
>>> IntegrationTest.plotting_options.activated=(
...     fluxes.qin, fluxes.qout)
>>> test = IntegrationTest(
...     stream,
...     seqs=(fluxes.qin, fluxes.qpin, fluxes.qpout,
...           fluxes.qout, nodes.output.sequences.sim))

To start the respective example runs from stationary conditions, a base flow value of
2 m³/s is set for all values of the log sequences |LogIn| and |LogOut|:

>>> test.inits = ((logs.login, 2.0),
...               (logs.logout, 2.0))

We want to print just the time instead of the whole date:

>>> test.dateformat = "%H:%M"

We define two flood events, one for each inlet node:

>>> nodes.input1.sequences.sim.series = (
...     1.0, 1.0, 2.0, 4.0, 3.0, 2.0, 1.0, 1.0, 1.0, 1.0,
...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
>>> nodes.input2.sequences.sim.series = (
...     1.0, 2.0, 6.0, 9.0, 8.0, 6.0, 4.0, 3.0, 2.0, 1.0,
...     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)

.. _arma_rimorido_ma:

MA coefficients
_______________

In the first example, we define a pure fourth-order moving average (MA) process via the
control parameter |Responses|:

>>> responses(((), (0.2, 0.4, 0.3, 0.1)))

This configuration leads to a usual "unit hydrograph" convolution result, where all
inflow "impulses" are separated into the actual and the three subsequent time steps:

.. integration-test::

    >>> test("arma_rimorido_ma")
    |  date |  qin | qpin | qpout | qout | output |
    -----------------------------------------------
    | 00:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 01:00 |  3.0 |  3.0 |   2.2 |  2.2 |    2.2 |
    | 02:00 |  8.0 |  8.0 |   3.6 |  3.6 |    3.6 |
    | 03:00 | 13.0 | 13.0 |   6.9 |  6.9 |    6.9 |
    | 04:00 | 11.0 | 11.0 |  10.1 | 10.1 |   10.1 |
    | 05:00 |  8.0 |  8.0 |  10.7 | 10.7 |   10.7 |
    | 06:00 |  5.0 |  5.0 |   8.8 |  8.8 |    8.8 |
    | 07:00 |  4.0 |  4.0 |   6.3 |  6.3 |    6.3 |
    | 08:00 |  3.0 |  3.0 |   4.5 |  4.5 |    4.5 |
    | 09:00 |  2.0 |  2.0 |   3.3 |  3.3 |    3.3 |
    | 10:00 |  2.0 |  2.0 |   2.5 |  2.5 |    2.5 |
    | 11:00 |  2.0 |  2.0 |   2.1 |  2.1 |    2.1 |
    | 12:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 13:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 14:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 15:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 16:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 17:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 18:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 19:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |

.. _arma_rimorido_arma:

ARMA coefficients
_________________

Now, we set the order of the MA process to the smallest possible value, which is one.
The autoregression (AR) process is of order two.  Note that negative AR coefficients
are allowed (also note the opposite signs of the coefficients in contrast to the
statistical literature):

>>> responses(((1.1, -0.3), (0.2,)))

Due to the AR process, the maximum time delay of some fractions of each input impulse
is theoretically infinite:

.. integration-test::

    >>> test("arma_rimorido_arma")
    |  date |  qin | qpin |    qpout |     qout |   output |
    --------------------------------------------------------
    | 00:00 |  2.0 |  2.0 |      2.0 |      2.0 |      2.0 |
    | 01:00 |  3.0 |  3.0 |      2.2 |      2.2 |      2.2 |
    | 02:00 |  8.0 |  8.0 |     3.42 |     3.42 |     3.42 |
    | 03:00 | 13.0 | 13.0 |    5.702 |    5.702 |    5.702 |
    | 04:00 | 11.0 | 11.0 |   7.4462 |   7.4462 |   7.4462 |
    | 05:00 |  8.0 |  8.0 |  8.08022 |  8.08022 |  8.08022 |
    | 06:00 |  5.0 |  5.0 | 7.654382 | 7.654382 | 7.654382 |
    | 07:00 |  4.0 |  4.0 | 6.795754 | 6.795754 | 6.795754 |
    | 08:00 |  3.0 |  3.0 | 5.779015 | 5.779015 | 5.779015 |
    | 09:00 |  2.0 |  2.0 |  4.71819 |  4.71819 |  4.71819 |
    | 10:00 |  2.0 |  2.0 | 3.856305 | 3.856305 | 3.856305 |
    | 11:00 |  2.0 |  2.0 | 3.226478 | 3.226478 | 3.226478 |
    | 12:00 |  2.0 |  2.0 | 2.792235 | 2.792235 | 2.792235 |
    | 13:00 |  2.0 |  2.0 | 2.503515 | 2.503515 | 2.503515 |
    | 14:00 |  2.0 |  2.0 | 2.316196 | 2.316196 | 2.316196 |
    | 15:00 |  2.0 |  2.0 | 2.196761 | 2.196761 | 2.196761 |
    | 16:00 |  2.0 |  2.0 | 2.121578 | 2.121578 | 2.121578 |
    | 17:00 |  2.0 |  2.0 | 2.074708 | 2.074708 | 2.074708 |
    | 18:00 |  2.0 |  2.0 | 2.045705 | 2.045705 | 2.045705 |
    | 19:00 |  2.0 |  2.0 | 2.027863 | 2.027863 | 2.027863 |

.. _arma_rimorido_delay:

Increased delay
_______________

This example is identical to the second one, except for the additional time delay of
exactly one hour due to the changed MA process:

>>> responses(((1.1, -0.3), (0.0, 0.2)))

.. integration-test::

    >>> test("arma_rimorido_delay")
    |  date |  qin | qpin |    qpout |     qout |   output |
    --------------------------------------------------------
    | 00:00 |  2.0 |  2.0 |      2.0 |      2.0 |      2.0 |
    | 01:00 |  3.0 |  3.0 |      2.0 |      2.0 |      2.0 |
    | 02:00 |  8.0 |  8.0 |      2.2 |      2.2 |      2.2 |
    | 03:00 | 13.0 | 13.0 |     3.42 |     3.42 |     3.42 |
    | 04:00 | 11.0 | 11.0 |    5.702 |    5.702 |    5.702 |
    | 05:00 |  8.0 |  8.0 |   7.4462 |   7.4462 |   7.4462 |
    | 06:00 |  5.0 |  5.0 |  8.08022 |  8.08022 |  8.08022 |
    | 07:00 |  4.0 |  4.0 | 7.654382 | 7.654382 | 7.654382 |
    | 08:00 |  3.0 |  3.0 | 6.795754 | 6.795754 | 6.795754 |
    | 09:00 |  2.0 |  2.0 | 5.779015 | 5.779015 | 5.779015 |
    | 10:00 |  2.0 |  2.0 |  4.71819 |  4.71819 |  4.71819 |
    | 11:00 |  2.0 |  2.0 | 3.856305 | 3.856305 | 3.856305 |
    | 12:00 |  2.0 |  2.0 | 3.226478 | 3.226478 | 3.226478 |
    | 13:00 |  2.0 |  2.0 | 2.792235 | 2.792235 | 2.792235 |
    | 14:00 |  2.0 |  2.0 | 2.503515 | 2.503515 | 2.503515 |
    | 15:00 |  2.0 |  2.0 | 2.316196 | 2.316196 | 2.316196 |
    | 16:00 |  2.0 |  2.0 | 2.196761 | 2.196761 | 2.196761 |
    | 17:00 |  2.0 |  2.0 | 2.121578 | 2.121578 | 2.121578 |
    | 18:00 |  2.0 |  2.0 | 2.074708 | 2.074708 | 2.074708 |
    | 19:00 |  2.0 |  2.0 | 2.045705 | 2.045705 | 2.045705 |

.. _arma_rimorido_negative_discharge:

Negative discharge
__________________

In some hydrological applications, the inflow into a channel might sometimes be lower
than 0 m³/s.  |arma_rimorido| generally routes such negative discharges using the
response function with the lowest discharge threshold.  When we repeat the calculation
of the :ref:`arma_rimorido_delay` example with inflow constantly decreased by 3 m³/s,
the outflow is also constantly decreased by 3 m³/s, and many simulated values are
negative:

.. integration-test::

    >>> nodes.input1.sequences.sim.series -= 3.0
    >>> test.inits = ((logs.login, -1.0),
    ...               (logs.logout, -1.0))
    >>> test("arma_rimorido_negative_discharge")
    |  date |  qin | qpin |     qpout |      qout |    output |
    -----------------------------------------------------------
    | 00:00 | -1.0 | -1.0 |      -1.0 |      -1.0 |      -1.0 |
    | 01:00 |  0.0 |  0.0 |      -1.0 |      -1.0 |      -1.0 |
    | 02:00 |  5.0 |  5.0 |      -0.8 |      -0.8 |      -0.8 |
    | 03:00 | 10.0 | 10.0 |      0.42 |      0.42 |      0.42 |
    | 04:00 |  8.0 |  8.0 |     2.702 |     2.702 |     2.702 |
    | 05:00 |  5.0 |  5.0 |    4.4462 |    4.4462 |    4.4462 |
    | 06:00 |  2.0 |  2.0 |   5.08022 |   5.08022 |   5.08022 |
    | 07:00 |  1.0 |  1.0 |  4.654382 |  4.654382 |  4.654382 |
    | 08:00 |  0.0 |  0.0 |  3.795754 |  3.795754 |  3.795754 |
    | 09:00 | -1.0 | -1.0 |  2.779015 |  2.779015 |  2.779015 |
    | 10:00 | -1.0 | -1.0 |   1.71819 |   1.71819 |   1.71819 |
    | 11:00 | -1.0 | -1.0 |  0.856305 |  0.856305 |  0.856305 |
    | 12:00 | -1.0 | -1.0 |  0.226478 |  0.226478 |  0.226478 |
    | 13:00 | -1.0 | -1.0 | -0.207765 | -0.207765 | -0.207765 |
    | 14:00 | -1.0 | -1.0 | -0.496485 | -0.496485 | -0.496485 |
    | 15:00 | -1.0 | -1.0 | -0.683804 | -0.683804 | -0.683804 |
    | 16:00 | -1.0 | -1.0 | -0.803239 | -0.803239 | -0.803239 |
    | 17:00 | -1.0 | -1.0 | -0.878422 | -0.878422 | -0.878422 |
    | 18:00 | -1.0 | -1.0 | -0.925292 | -0.925292 | -0.925292 |
    | 19:00 | -1.0 | -1.0 | -0.954295 | -0.954295 | -0.954295 |

>>> nodes.input1.sequences.sim.series += 3.0
>>> test.inits = ((logs.login, 2.0),
...               (logs.logout, 2.0))

.. _arma_rimorido_plausibility:

Plausibility
____________

Be aware that neither parameter |Responses| checks the assigned coefficients nor does
|arma_rimorido| check the calculated outflow for plausibility (one can use the features
provided in modules |iuhtools| and |armatools| to calculate reliable coefficients).
The fourth example increases the span of the AR coefficients used in the third example.
The complete ARMA process is still mass conservative, but some response values of the
recession curve are negative:

.. integration-test::

    >>> responses(((1.5, -0.7), (0.0, 0.2)))
    >>> test("arma_rimorido_plausibility")
    |  date |  qin | qpin |     qpout |      qout |    output |
    -----------------------------------------------------------
    | 00:00 |  2.0 |  2.0 |       2.0 |       2.0 |       2.0 |
    | 01:00 |  3.0 |  3.0 |       2.0 |       2.0 |       2.0 |
    | 02:00 |  8.0 |  8.0 |       2.2 |       2.2 |       2.2 |
    | 03:00 | 13.0 | 13.0 |       3.5 |       3.5 |       3.5 |
    | 04:00 | 11.0 | 11.0 |      6.31 |      6.31 |      6.31 |
    | 05:00 |  8.0 |  8.0 |     9.215 |     9.215 |     9.215 |
    | 06:00 |  5.0 |  5.0 |   11.0055 |   11.0055 |   11.0055 |
    | 07:00 |  4.0 |  4.0 |  11.05775 |  11.05775 |  11.05775 |
    | 08:00 |  3.0 |  3.0 |  9.682775 |  9.682775 |  9.682775 |
    | 09:00 |  2.0 |  2.0 |  7.383738 |  7.383738 |  7.383738 |
    | 10:00 |  2.0 |  2.0 |  4.697664 |  4.697664 |  4.697664 |
    | 11:00 |  2.0 |  2.0 |  2.277879 |  2.277879 |  2.277879 |
    | 12:00 |  2.0 |  2.0 |  0.528454 |  0.528454 |  0.528454 |
    | 13:00 |  2.0 |  2.0 | -0.401834 | -0.401834 | -0.401834 |
    | 14:00 |  2.0 |  2.0 | -0.572669 | -0.572669 | -0.572669 |
    | 15:00 |  2.0 |  2.0 |  -0.17772 |  -0.17772 |  -0.17772 |
    | 16:00 |  2.0 |  2.0 |  0.534289 |  0.534289 |  0.534289 |
    | 17:00 |  2.0 |  2.0 |  1.325837 |  1.325837 |  1.325837 |
    | 18:00 |  2.0 |  2.0 |  2.014753 |  2.014753 |  2.014753 |
    | 19:00 |  2.0 |  2.0 |  2.494044 |  2.494044 |  2.494044 |

.. _arma_rimorido_nonlinearity:

Nonlinearity
____________

In the following example, we combine the coefficients of the first two examples.
Between inflow values of 0 and 7 m³/s, the pure AR process is applied.  For inflow
discharges exceeding 7 m³/s, inflow is separated.  The AR process is still applied on
the portion of 7 m³/s, but for the inflow exceeding this threshold, the mixed ARMA
model is applied:

>>> responses(_0=((), (0.2, 0.4, 0.3, 0.1)),
...           _7=((1.1, -0.3), (0.2,)))

To start from stationary conditions again, one has to apply different values to both
log sequences.  The base flow value of 2 m³/s is only given to the (low flow) MA model;
the (high flow) ARMA model is initialized with zero values instead:

>>> test.inits.login = [[2.0], [0.0]]
>>> test.inits.logout = [[2.0], [0.0]]

The separate handling of the inflow can be studied by inspecting the columns of
sequence |QPIn| and sequence |QPOut|.  The respective left columns show the input and
output of the MA model, and the respective right columns show the input and output of
the ARMA model:

.. integration-test::

    >>> test("arma_rimorido_nonlinearity")
    |  date |  qin |      qpin |         qpout |     qout |   output |
    ------------------------------------------------------------------
    | 00:00 |  2.0 | 2.0   0.0 | 2.0       0.0 |      2.0 |      2.0 |
    | 01:00 |  3.0 | 3.0   0.0 | 2.2       0.0 |      2.2 |      2.2 |
    | 02:00 |  8.0 | 7.0   1.0 | 3.4       0.2 |      3.6 |      3.6 |
    | 03:00 | 13.0 | 7.0   6.0 | 5.3      1.42 |     6.72 |     6.72 |
    | 04:00 | 11.0 | 7.0   4.0 | 6.6     2.302 |    8.902 |    8.902 |
    | 05:00 |  8.0 | 7.0   1.0 | 7.0    2.3062 |   9.3062 |   9.3062 |
    | 06:00 |  5.0 | 5.0   0.0 | 6.6   1.84622 |  8.44622 |  8.44622 |
    | 07:00 |  4.0 | 4.0   0.0 | 5.6  1.338982 | 6.938982 | 6.938982 |
    | 08:00 |  3.0 | 3.0   0.0 | 4.4  0.919014 | 5.319014 | 5.319014 |
    | 09:00 |  2.0 | 2.0   0.0 | 3.3  0.609221 | 3.909221 | 3.909221 |
    | 10:00 |  2.0 | 2.0   0.0 | 2.5  0.394439 | 2.894439 | 2.894439 |
    | 11:00 |  2.0 | 2.0   0.0 | 2.1  0.251116 | 2.351116 | 2.351116 |
    | 12:00 |  2.0 | 2.0   0.0 | 2.0  0.157896 | 2.157896 | 2.157896 |
    | 13:00 |  2.0 | 2.0   0.0 | 2.0  0.098351 | 2.098351 | 2.098351 |
    | 14:00 |  2.0 | 2.0   0.0 | 2.0  0.060817 | 2.060817 | 2.060817 |
    | 15:00 |  2.0 | 2.0   0.0 | 2.0  0.037394 | 2.037394 | 2.037394 |
    | 16:00 |  2.0 | 2.0   0.0 | 2.0  0.022888 | 2.022888 | 2.022888 |
    | 17:00 |  2.0 | 2.0   0.0 | 2.0  0.013959 | 2.013959 | 2.013959 |
    | 18:00 |  2.0 | 2.0   0.0 | 2.0  0.008488 | 2.008488 | 2.008488 |
    | 19:00 |  2.0 | 2.0   0.0 | 2.0  0.005149 | 2.005149 | 2.005149 |
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

# ...from arma
from hydpy.models.arma import arma_model


class Model(modeltools.AdHocModel):
    """|arma_rimorido.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="ARMA-RIMO/RIDO",
        description="nonlinear routing by multiple ARMA processes",
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = (arma_model.Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        arma_model.Calc_QPIn_V1,
        arma_model.Update_LogIn_V1,
        arma_model.Calc_QMA_V1,
        arma_model.Calc_QAR_V1,
        arma_model.Calc_QPOut_V1,
        arma_model.Update_LogOut_V1,
        arma_model.Calc_QOut_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (arma_model.Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
