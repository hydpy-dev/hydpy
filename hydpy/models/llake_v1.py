# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""
The LARSIM-Lake version of HydPy-L-Lake (called llake_v1) is a simple lake
model. Its continuity equation is primarily solved via a central finite
difference approach.  It allows for an arbitrary number of inflows and
determines a single outflow value for each simulation time step.
The relationships between water stage, water volume and the associated
outflow are defined via vectors.  Between/beyond the triples defined by
these vectors, linear interpolation/extrapolation is performed.
The outflow vector is allowed to vary with seasonal pattern.  Therefore,
different vectors for different times of the year need to be defined.
Again, between these dates linear interpolation is performed to gain
intermediate vectors.

Two additional features are implemented.  Firstly, one can define a
maximum drop of the water stage, which is not exceeded even when the
triples of  water state, water volume and outflow indicate so.
Secondly, water can be added to or substracted from the outflow
calculated beforehand.  Both associated scalar parameters are allowed
to vary in time, as explained for the outflow vector.

Note that the accuracy of the results calculated by lake_v1 depend
on the internal step size parameter |MaxDT|.

Integration examples:

    The following calculations are performed over a period of 20 days:

    >>> from hydpy import pub, Nodes, Element
    >>> pub.timegrids = '01.01.2000', '21.01.2000', '1d'

    Import the model and define the time settings:

    >>> from hydpy.models.llake_v1 import *
    >>> parameterstep('1d')

    For testing purposes, the model input shall be retrieved from the nodes
    `input1` and `input2` and the model output shall be passed to node
    `output`.  Firstly, define all nodes:

    >>> nodes = Nodes('input1', 'input2', 'output')

    Secondly, define the element "lake" and build the connections between
    the nodes defined above and the `llake_v1` model instance:

    >>> lake = Element('lake', inlets=['input1', 'input2'], outlets='output')
    >>> lake.connect(model)

    Prepare a test function object, which prints the respective values of
    the model sequences `qz`, `qa`, `v`, and `w`.  The node sequence `sim`
    is added in order to prove that the values calculated for `qa` are
    actually passed to `sim`:

    >>> from hydpy import IntegrationTest
    >>> test = IntegrationTest(lake,
    ...                        seqs=(fluxes.qz, fluxes.qa,
    ...                              nodes.output.sequences.sim,
    ...                              states.v, states.w),
    ...                        inits=((states.v, 0.),
    ...                               (states.w, 0.)))
    >>> test.dateformat = '%d.%m.'

    Set the values of those control parameter, which remain fixed for all
    three example simulations, in the most simple manner:

    >>> n(2)
    >>> w(0., 1.)
    >>> v(0., 1e6)
    >>> q(0., 10.)
    >>> maxdt('1d')

    Define two flood events, one for each lake inflow:

    >>> nodes.input1.sequences.sim.series = [
    ...                         0., 0., 1., 3., 2., 1., 0., 0., 0., 0.,
    ...                         0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    >>> nodes.input2.sequences.sim.series = [
    ...                         0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...                         0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]

    In the first example, neither a restriction regarding the maximum
    water drop nor a water abstraction is defined.  Hence the sums of
    the total input (qz) and of the final output (identical with qa) are
    nearly the same.  The maximum of the final output occurs when
    the falling limb of qz intersects with qa:

    >>> maxdw(.0)
    >>> verzw(0.)
    >>> test()
    |   date |   qz |       qa |   output |             v |        w |
    ------------------------------------------------------------------
    | 01.01. |  0.0 |      0.0 |      0.0 |           0.0 |      0.0 |
    | 02.01. |  1.0 | 0.301676 | 0.301676 |  60335.195531 | 0.060335 |
    | 03.01. |  6.0 | 2.231391 | 2.231391 | 385943.010518 | 0.385943 |
    | 04.01. | 12.0 | 6.315244 | 6.315244 | 877105.886853 | 0.877106 |
    | 05.01. | 10.0 | 9.141801 | 9.141801 | 951254.290316 | 0.951254 |
    | 06.01. |  6.0 | 8.452893 | 8.452893 | 739324.327444 | 0.739324 |
    | 07.01. |  3.0 | 6.067907 | 6.067907 | 474257.135467 | 0.474257 |
    | 08.01. |  2.0 | 3.915203 | 3.915203 | 308783.556526 | 0.308784 |
    | 09.01. |  1.0 | 2.457986 | 2.457986 |  182813.58946 | 0.182814 |
    | 10.01. |  0.0 | 1.276631 | 1.276631 |  72512.652803 | 0.072513 |
    | 11.01. |  0.0 | 0.506373 | 0.506373 |   28762.00195 | 0.028762 |
    | 12.01. |  0.0 | 0.200852 | 0.200852 |  11408.391835 | 0.011408 |
    | 13.01. |  0.0 | 0.079668 | 0.079668 |   4525.116314 | 0.004525 |
    | 14.01. |  0.0 |   0.0316 |   0.0316 |   1794.878538 | 0.001795 |
    | 15.01. |  0.0 | 0.012534 | 0.012534 |    711.935063 | 0.000712 |
    | 16.01. |  0.0 | 0.004972 | 0.004972 |    282.387651 | 0.000282 |
    | 17.01. |  0.0 | 0.001972 | 0.001972 |    112.008509 | 0.000112 |
    | 18.01. |  0.0 | 0.000782 | 0.000782 |     44.427956 | 0.000044 |
    | 19.01. |  0.0 |  0.00031 |  0.00031 |     17.622262 | 0.000018 |
    | 20.01. |  0.0 | 0.000123 | 0.000123 |      6.989836 | 0.000007 |

    When the maximum water drop is set to 0.1 m/d, the resulting
    outflow hydrograph shows a plateau in its falling limb.  This
    plateau is placed in the time period, where little inflow occurs
    but the (potential) outflow is still high, due to large amounts
    of stored water.  In this time period, qa is limited by the
    maximum water drop allowed:

    >>> maxdw(.1)
    >>> verzw(0.)
    >>> test()
    |   date |   qz |       qa |   output |             v |        w |
    ------------------------------------------------------------------
    | 01.01. |  0.0 |      0.0 |      0.0 |           0.0 |      0.0 |
    | 02.01. |  1.0 | 0.301676 | 0.301676 |  60335.195531 | 0.060335 |
    | 03.01. |  6.0 | 2.231391 | 2.231391 | 385943.010518 | 0.385943 |
    | 04.01. | 12.0 | 6.315244 | 6.315244 | 877105.886853 | 0.877106 |
    | 05.01. | 10.0 | 9.141801 | 9.141801 | 951254.290316 | 0.951254 |
    | 06.01. |  6.0 | 7.157407 | 7.157407 | 851254.290316 | 0.851254 |
    | 07.01. |  3.0 | 4.157407 | 4.157407 | 751254.290316 | 0.751254 |
    | 08.01. |  2.0 | 3.157407 | 3.157407 | 651254.290316 | 0.651254 |
    | 09.01. |  1.0 | 2.157407 | 2.157407 | 551254.290316 | 0.551254 |
    | 10.01. |  0.0 | 1.157407 | 1.157407 | 451254.290316 | 0.451254 |
    | 11.01. |  0.0 | 1.157407 | 1.157407 | 351254.290316 | 0.351254 |
    | 12.01. |  0.0 | 1.157407 | 1.157407 | 251254.290316 | 0.251254 |
    | 13.01. |  0.0 | 1.157407 | 1.157407 | 151254.290316 | 0.151254 |
    | 14.01. |  0.0 | 1.056245 | 1.056245 |  59994.718505 | 0.059995 |
    | 15.01. |  0.0 | 0.418958 | 0.418958 |  23796.787787 | 0.023797 |
    | 16.01. |  0.0 | 0.166179 | 0.166179 |   9438.949346 | 0.009439 |
    | 17.01. |  0.0 | 0.065914 | 0.065914 |   3743.940802 | 0.003744 |
    | 18.01. |  0.0 | 0.026145 | 0.026145 |   1485.026799 | 0.001485 |
    | 19.01. |  0.0 |  0.01037 |  0.01037 |    589.032976 | 0.000589 |
    | 20.01. |  0.0 | 0.004113 | 0.004113 |    233.638778 | 0.000234 |

    In the above example, the water balance is still maintained.  This
    is not the case for the last example, where 1 m³/s is subtracted
    from the total outflow.  Regarding its peak time and form, the
    output hydrograph is identical/similar to the one of the first
    example:

    >>> maxdw(.0)
    >>> verzw(1.)
    >>> test()
    |   date |   qz |       qa |   output |             v |        w |
    ------------------------------------------------------------------
    | 01.01. |  0.0 |      0.0 |      0.0 |           0.0 |      0.0 |
    | 02.01. |  1.0 |      0.0 |      0.0 |  60335.195531 | 0.060335 |
    | 03.01. |  6.0 | 1.231391 | 1.231391 | 385943.010518 | 0.385943 |
    | 04.01. | 12.0 | 5.315244 | 5.315244 | 877105.886853 | 0.877106 |
    | 05.01. | 10.0 | 8.141801 | 8.141801 | 951254.290316 | 0.951254 |
    | 06.01. |  6.0 | 7.452893 | 7.452893 | 739324.327444 | 0.739324 |
    | 07.01. |  3.0 | 5.067907 | 5.067907 | 474257.135467 | 0.474257 |
    | 08.01. |  2.0 | 2.915203 | 2.915203 | 308783.556526 | 0.308784 |
    | 09.01. |  1.0 | 1.457986 | 1.457986 |  182813.58946 | 0.182814 |
    | 10.01. |  0.0 | 0.276631 | 0.276631 |  72512.652803 | 0.072513 |
    | 11.01. |  0.0 |      0.0 |      0.0 |   28762.00195 | 0.028762 |
    | 12.01. |  0.0 |      0.0 |      0.0 |  11408.391835 | 0.011408 |
    | 13.01. |  0.0 |      0.0 |      0.0 |   4525.116314 | 0.004525 |
    | 14.01. |  0.0 |      0.0 |      0.0 |   1794.878538 | 0.001795 |
    | 15.01. |  0.0 |      0.0 |      0.0 |    711.935063 | 0.000712 |
    | 16.01. |  0.0 |      0.0 |      0.0 |    282.387651 | 0.000282 |
    | 17.01. |  0.0 |      0.0 |      0.0 |    112.008509 | 0.000112 |
    | 18.01. |  0.0 |      0.0 |      0.0 |     44.427956 | 0.000044 |
    | 19.01. |  0.0 |      0.0 |      0.0 |     17.622262 | 0.000018 |
    | 20.01. |  0.0 |      0.0 |      0.0 |      6.989836 | 0.000007 |

    In the following, the given examples above repeated.  The only
    parameter that will be altered is the internal simulation step size,
    being one hour instead of one day:

    >>> maxdt('1h')
    >>> model.parameters.update()

    Hence, the principles discussed above remain valid, but the result are
    a little more accurate.

    Repetition of the first experiment:

    >>> maxdw(.0)
    >>> verzw(0.)
    >>> test()
    |   date |   qz |       qa |   output |             v |        w |
    ------------------------------------------------------------------
    | 01.01. |  0.0 |      0.0 |      0.0 |           0.0 |      0.0 |
    | 02.01. |  1.0 | 0.330363 | 0.330363 |  57856.651951 | 0.057857 |
    | 03.01. |  6.0 | 2.369607 | 2.369607 | 371522.641905 | 0.371523 |
    | 04.01. | 12.0 | 6.452208 | 6.452208 | 850851.903469 | 0.850852 |
    | 05.01. | 10.0 | 9.001249 | 9.001249 |  937143.99857 | 0.937144 |
    | 06.01. |  6.0 | 8.257642 | 8.257642 | 742083.768745 | 0.742084 |
    | 07.01. |  3.0 | 5.960357 | 5.960357 | 486308.901331 | 0.486309 |
    | 08.01. |  2.0 | 3.917231 | 3.917231 | 320660.156784 |  0.32066 |
    | 09.01. |  1.0 | 2.477622 | 2.477622 |  192993.57788 | 0.192994 |
    | 10.01. |  0.0 | 1.292357 | 1.292357 |  81333.955239 | 0.081334 |
    | 11.01. |  0.0 | 0.544642 | 0.544642 |  34276.851838 | 0.034277 |
    | 12.01. |  0.0 | 0.229531 | 0.229531 |  14445.412971 | 0.014445 |
    | 13.01. |  0.0 | 0.096732 | 0.096732 |   6087.780665 | 0.006088 |
    | 14.01. |  0.0 | 0.040766 | 0.040766 |   2565.594594 | 0.002566 |
    | 15.01. |  0.0 |  0.01718 |  0.01718 |   1081.227459 | 0.001081 |
    | 16.01. |  0.0 |  0.00724 |  0.00724 |    455.665451 | 0.000456 |
    | 17.01. |  0.0 | 0.003051 | 0.003051 |    192.032677 | 0.000192 |
    | 18.01. |  0.0 | 0.001286 | 0.001286 |     80.928999 | 0.000081 |
    | 19.01. |  0.0 | 0.000542 | 0.000542 |      34.10619 | 0.000034 |
    | 20.01. |  0.0 | 0.000228 | 0.000228 |      14.37349 | 0.000014 |

    Repetition of the second experiment:

    >>> maxdw(.1)
    >>> verzw(0.)
    >>> test()
    |   date |   qz |       qa |   output |             v |        w |
    ------------------------------------------------------------------
    | 01.01. |  0.0 |      0.0 |      0.0 |           0.0 |      0.0 |
    | 02.01. |  1.0 | 0.330363 | 0.330363 |  57856.651951 | 0.057857 |
    | 03.01. |  6.0 | 2.369607 | 2.369607 | 371522.641905 | 0.371523 |
    | 04.01. | 12.0 | 6.452208 | 6.452208 | 850851.903469 | 0.850852 |
    | 05.01. | 10.0 | 9.001249 | 9.001249 |  937143.99857 | 0.937144 |
    | 06.01. |  6.0 | 7.157407 | 7.157407 |  837143.99857 | 0.837144 |
    | 07.01. |  3.0 | 4.157407 | 4.157407 |  737143.99857 | 0.737144 |
    | 08.01. |  2.0 | 3.157407 | 3.157407 |  637143.99857 | 0.637144 |
    | 09.01. |  1.0 | 2.157407 | 2.157407 |  537143.99857 | 0.537144 |
    | 10.01. |  0.0 | 1.157407 | 1.157407 |  437143.99857 | 0.437144 |
    | 11.01. |  0.0 | 1.157407 | 1.157407 |  337143.99857 | 0.337144 |
    | 12.01. |  0.0 | 1.157407 | 1.157407 |  237143.99857 | 0.237144 |
    | 13.01. |  0.0 | 1.157407 | 1.157407 |  137143.99857 | 0.137144 |
    | 14.01. |  0.0 | 0.918367 | 0.918367 |  57797.072646 | 0.057797 |
    | 15.01. |  0.0 | 0.387031 | 0.387031 |  24357.621488 | 0.024358 |
    | 16.01. |  0.0 | 0.163108 | 0.163108 |    10265.1172 | 0.010265 |
    | 17.01. |  0.0 | 0.068739 | 0.068739 |   4326.064069 | 0.004326 |
    | 18.01. |  0.0 | 0.028969 | 0.028969 |   1823.148238 | 0.001823 |
    | 19.01. |  0.0 | 0.012208 | 0.012208 |    768.335707 | 0.000768 |
    | 20.01. |  0.0 | 0.005145 | 0.005145 |    323.802391 | 0.000324 |

    Repetition of the third experiment:

    >>> maxdw(.0)
    >>> verzw(1.)
    >>> test()
    |   date |   qz |       qa |   output |             v |        w |
    ------------------------------------------------------------------
    | 01.01. |  0.0 |      0.0 |      0.0 |           0.0 |      0.0 |
    | 02.01. |  1.0 |      0.0 |      0.0 |  57856.651951 | 0.057857 |
    | 03.01. |  6.0 | 1.369607 | 1.369607 | 371522.641905 | 0.371523 |
    | 04.01. | 12.0 | 5.452208 | 5.452208 | 850851.903469 | 0.850852 |
    | 05.01. | 10.0 | 8.001249 | 8.001249 |  937143.99857 | 0.937144 |
    | 06.01. |  6.0 | 7.257642 | 7.257642 | 742083.768745 | 0.742084 |
    | 07.01. |  3.0 | 4.960357 | 4.960357 | 486308.901331 | 0.486309 |
    | 08.01. |  2.0 | 2.917231 | 2.917231 | 320660.156784 |  0.32066 |
    | 09.01. |  1.0 | 1.477622 | 1.477622 |  192993.57788 | 0.192994 |
    | 10.01. |  0.0 | 0.292357 | 0.292357 |  81333.955239 | 0.081334 |
    | 11.01. |  0.0 |      0.0 |      0.0 |  34276.851838 | 0.034277 |
    | 12.01. |  0.0 |      0.0 |      0.0 |  14445.412971 | 0.014445 |
    | 13.01. |  0.0 |      0.0 |      0.0 |   6087.780665 | 0.006088 |
    | 14.01. |  0.0 |      0.0 |      0.0 |   2565.594594 | 0.002566 |
    | 15.01. |  0.0 |      0.0 |      0.0 |   1081.227459 | 0.001081 |
    | 16.01. |  0.0 |      0.0 |      0.0 |    455.665451 | 0.000456 |
    | 17.01. |  0.0 |      0.0 |      0.0 |    192.032677 | 0.000192 |
    | 18.01. |  0.0 |      0.0 |      0.0 |     80.928999 | 0.000081 |
    | 19.01. |  0.0 |      0.0 |      0.0 |      34.10619 | 0.000034 |
    | 20.01. |  0.0 |      0.0 |      0.0 |      14.37349 | 0.000014 |
"""
# import...
# ...from standard library
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from HydPy
from hydpy.exe.modelimports import *
# ...from llake
from hydpy.models.llake import llake_model
from hydpy.models.llake import llake_control
from hydpy.models.llake import llake_derived
from hydpy.models.llake import llake_fluxes
from hydpy.models.llake import llake_states
from hydpy.models.llake import llake_aides
from hydpy.models.llake import llake_inlets
from hydpy.models.llake import llake_outlets


class Model(modeltools.Model):
    """LARSIM-Lake version of HydPy-L-Lake (llake_v1)."""
    _INLET_METHODS = (llake_model.pick_q_v1,)
    _RUN_METHODS = (llake_model.solve_dv_dt_v1,
                    llake_model.interp_w_v1,
                    llake_model.corr_dw_v1,
                    llake_model.modify_qa_v1,)
    _ADD_METHODS = (llake_model.interp_v_v1,
                    llake_model.calc_vq_v1,
                    llake_model.interp_qa_v1,
                    llake_model.calc_v_qa_v1)
    _OUTLET_METHODS = (llake_model.pass_q_v1,)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of llake_v1, directly defined by the user."""
    CLASSES = (llake_control.N,
               llake_control.W,
               llake_control.V,
               llake_control.Q,
               llake_control.MaxDT,
               llake_control.MaxDW,
               llake_control.Verzw)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of llake_v1, indirectly defined by the user.
    """
    CLASSES = (llake_derived.TOY,
               llake_derived.Seconds,
               llake_derived.NmbSubsteps,
               llake_derived.VQ)


class StateSequences(sequencetools.StateSequences):
    """State sequences of llake_v1."""
    CLASSES = (llake_states.V,
               llake_states.W)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of llake_v1."""
    CLASSES = (llake_fluxes.QZ,
               llake_fluxes.QA)


class AideSequences(sequencetools.AideSequences):
    """Aide sequences of llake_v1."""
    CLASSES = (llake_aides.QA,
               llake_aides.VQ,
               llake_aides.V,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of llake_v1."""
    CLASSES = (llake_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of llake_v1."""
    CLASSES = (llake_outlets.Q,)


autodoc_applicationmodel()

# pylint: disable=invalid-name
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
