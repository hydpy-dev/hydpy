# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Controlled lake (SEEG) version of HydPy-Dam.

Conceptionally, |dam_v006| corresponds to the "controlled lake" model of
LARSIM (selectable via the "SEEG" option) and therefore to application model
|llake_v1|.  On the technical side, it contrasts to |llake_v1|.  Like for
all models of the HydPy-D family, we implemented its methods as continuous
ordinary differential equations. Please read the documentation on the
application model |dam_v001| to get an understanding of the basics of
application model |dam_v006|.  Especially, you should read how to set proper
smoothing parameter values and how to configure the artificial neural
networks used to model the relationships between stage and volume and
between discharge and stage.

Integration examples:

    We shortly repeat the first and the second example of the documentation
    on application model |llake_v1| (but use|dam_v006|, of course).  The
    "spatial" setting is identical, except that |dam_v006| allows for only
    one inlet node:

    >>> from hydpy import pub, Node, Element
    >>> pub.timegrids = '01.01.2000', '21.01.2000', '1d'
    >>> from hydpy.models.dam_v006 import *
    >>> parameterstep('1d')
    >>> input_ = Node('input_')
    >>> output = Node('output')
    >>> lake = Element('lake', inlets=input_, outlets=output)
    >>> lake.model = model
    >>> from hydpy import IntegrationTest
    >>> test = IntegrationTest(lake,
    ...                        inits=[(states.watervolume, 0.0)])
    >>> test.dateformat = '%d.%m.'

    As in the examples on |llake_v1|, we use (approximately) linear
    relationships between |WaterLevel| and |WaterVolume| and
    |FloodDischarge| and |WaterLevel|, respectively (you can inspect
    the degree of linearity via method |anntools.SeasonalANN.plot|):

    >>> watervolume2waterlevel(
    ...     weights_input=1e-6, weights_output=4.e6,
    ...     intercepts_hidden=0.0, intercepts_output=-4e6/2)
    >>> waterlevel2flooddischarge(ann(
    ...     weights_input=1e-6, weights_output=4e7,
    ...     intercepts_hidden=0.0, intercepts_output=-4e7/2))

    For the first example, we set the |AllowedWaterLevelDrop| to the
    very large value of 10 m/d, to make sure this possible restriction
    does not affect the calculated lake outflow:

    >>> allowedwaterleveldrop(10.0)

    Additionally, we set the value of the related smoothing parameter
    |DischargeTolerance| to 0.1 m³/s:

    >>> dischargetolerance(0.1)

    The purpose of parameter |CatchmentArea| is to allow to determine
    reasonable default values for the parameter |AbsErrorMax| automatically,
    controlling the accuracy of the numerical integration process:

    >>> catchmentarea(86.4)
    >>> from hydpy import round_
    >>> round_(solver.abserrormax.INIT)
    0.01
    >>> parameters.update()
    >>> solver.abserrormax
    abserrormax(0.01)

    The inflow data is identical to the data of the example on application
    model |llake_v1| but supplied via one node only:

    >>> input_.sequences.sim.series = [
    ...     0.0, 1.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
    ...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    In the documentation on application model |llake_v1|, we calculate this
    first test case twice, choosing an internal integration step size of
    1 day and one hour in the first and the fourth example, respectively.
    The results of |dam_v006|, using its standard solver parameterisation,
    are more similar to the ones of the more accurate results of the hourly
    internal step size:

    >>> test('dam_v006_ex1a')
    |   date | inflow | flooddischarge |  outflow | watervolume | input_ |   output |
    ---------------------------------------------------------------------------------
    | 01.01. |    0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |       0.329814 | 0.329814 |    0.057904 |    1.0 | 0.329814 |
    | 03.01. |    6.0 |       2.370574 | 2.370574 |    0.371486 |    6.0 | 2.370574 |
    | 04.01. |   12.0 |       6.452959 | 6.452959 |    0.850751 |   12.0 | 6.452959 |
    | 05.01. |   10.0 |       8.999753 | 8.999753 |    0.937172 |   10.0 | 8.999753 |
    | 06.01. |    6.0 |       8.257426 | 8.257426 |    0.742131 |    6.0 | 8.257426 |
    | 07.01. |    3.0 |        5.96014 |  5.96014 |    0.486374 |    3.0 |  5.96014 |
    | 08.01. |    2.0 |       3.917326 | 3.917326 |    0.320717 |    2.0 | 3.917326 |
    | 09.01. |    1.0 |       2.477741 | 2.477741 |    0.193041 |    1.0 | 2.477741 |
    | 10.01. |    0.0 |       1.293731 | 1.293731 |    0.081262 |    0.0 | 1.293731 |
    | 11.01. |    0.0 |       0.544608 | 0.544608 |    0.034208 |    0.0 | 0.544608 |
    | 12.01. |    0.0 |       0.227669 | 0.227669 |    0.014537 |    0.0 | 0.227669 |
    | 13.01. |    0.0 |       0.096753 | 0.096753 |    0.006178 |    0.0 | 0.096753 |
    | 14.01. |    0.0 |       0.042778 | 0.042778 |    0.002482 |    0.0 | 0.042778 |
    | 15.01. |    0.0 |       0.017186 | 0.017186 |    0.000997 |    0.0 | 0.017186 |
    | 16.01. |    0.0 |       0.005664 | 0.005664 |    0.000508 |    0.0 | 0.005664 |
    | 17.01. |    0.0 |       0.002884 | 0.002884 |    0.000259 |    0.0 | 0.002884 |
    | 18.01. |    0.0 |       0.001469 | 0.001469 |    0.000132 |    0.0 | 0.001469 |
    | 19.01. |    0.0 |       0.000748 | 0.000748 |    0.000067 |    0.0 | 0.000748 |
    | 20.01. |    0.0 |       0.000381 | 0.000381 |    0.000034 |    0.0 | 0.000381 |

    .. raw:: html

        <a
            href="dam_v006_ex1a.html"
            target="_blank"
        >Click here to see the graph</a>

    |dam_v006| achieves this sufficiently high accuracy with 174 calls to
    the system of differential equations, which averages to less than nine
    calls per day:

    >>> model.numvars.nmb_calls
    174

    Through increasing the numerical tolerance, e.g. setting |AbsErrorMax|
    to 0.1 m³/s, we can gain some additional speedups without relevant
    deteriorations of the results (|dam_v006| usually achieves higher
    accuracies than indicated by the actual tolerance value):

    >>> model.numvars.nmb_calls = 0
    >>> solver.abserrormax(0.1)
    >>> test('dam_v006_ex1b')
    |   date | inflow | flooddischarge |  outflow | watervolume | input_ |   output |
    ---------------------------------------------------------------------------------
    | 01.01. |    0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |       0.334458 | 0.334458 |    0.057503 |    1.0 | 0.334458 |
    | 03.01. |    6.0 |        2.36426 |  2.36426 |    0.371631 |    6.0 |  2.36426 |
    | 04.01. |   12.0 |       6.448386 | 6.448386 |     0.85129 |   12.0 | 6.448386 |
    | 05.01. |   10.0 |       9.010274 | 9.010274 |    0.936803 |   10.0 | 9.010274 |
    | 06.01. |    6.0 |       8.241563 | 8.241563 |    0.743132 |    6.0 | 8.241563 |
    | 07.01. |    3.0 |       5.969805 | 5.969805 |     0.48654 |    3.0 | 5.969805 |
    | 08.01. |    2.0 |       3.907047 | 3.907047 |    0.321772 |    2.0 | 3.907047 |
    | 09.01. |    1.0 |       2.475983 | 2.475983 |    0.194247 |    1.0 | 2.475983 |
    | 10.01. |    0.0 |       1.292793 | 1.292793 |    0.082549 |    0.0 | 1.292793 |
    | 11.01. |    0.0 |         0.5494 |   0.5494 |    0.035081 |    0.0 |   0.5494 |
    | 12.01. |    0.0 |       0.242907 | 0.242907 |    0.014094 |    0.0 | 0.242907 |
    | 13.01. |    0.0 |       0.080053 | 0.080053 |    0.007177 |    0.0 | 0.080053 |
    | 14.01. |    0.0 |       0.040767 | 0.040767 |    0.003655 |    0.0 | 0.040767 |
    | 15.01. |    0.0 |       0.020761 | 0.020761 |    0.001861 |    0.0 | 0.020761 |
    | 16.01. |    0.0 |       0.010572 | 0.010572 |    0.000948 |    0.0 | 0.010572 |
    | 17.01. |    0.0 |       0.005384 | 0.005384 |    0.000483 |    0.0 | 0.005384 |
    | 18.01. |    0.0 |       0.002742 | 0.002742 |    0.000246 |    0.0 | 0.002742 |
    | 19.01. |    0.0 |       0.001396 | 0.001396 |    0.000125 |    0.0 | 0.001396 |
    | 20.01. |    0.0 |       0.000711 | 0.000711 |    0.000064 |    0.0 | 0.000711 |

    .. raw:: html

        <a
            href="dam_v006_ex1b.html"
            target="_blank"
        >Click here to see the graph</a>

    >>> model.numvars.nmb_calls
    104

    After setting |AllowedWaterLevelDrop| to 0.1 m/d, the resulting outflow
    hydrograph shows the same plateau in its falling limb as in the results
    of application model |llake_v1|.  Again, there a better agreement to
    the more precise results accomplished by an hourly stepsize (example 5)
    instead of a daily stepsize (example 2):

    >>> model.numvars.nmb_calls = 0
    >>> solver.abserrormax(0.01)
    >>> allowedwaterleveldrop(0.1)
    >>> test('dam_v006_ex2')
    |   date | inflow | flooddischarge |  outflow | watervolume | input_ |   output |
    ---------------------------------------------------------------------------------
    | 01.01. |    0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |       0.329814 | 0.329814 |    0.057904 |    1.0 | 0.329814 |
    | 03.01. |    6.0 |       2.370574 | 2.370574 |    0.371486 |    6.0 | 2.370574 |
    | 04.01. |   12.0 |       6.452959 | 6.452959 |    0.850751 |   12.0 | 6.452959 |
    | 05.01. |   10.0 |       8.999753 | 8.999753 |    0.937172 |   10.0 | 8.999753 |
    | 06.01. |    6.0 |        8.87243 | 7.155768 |    0.837314 |    6.0 | 7.155768 |
    | 07.01. |    3.0 |       7.873846 | 4.155768 |    0.737455 |    3.0 | 4.155768 |
    | 08.01. |    2.0 |       6.875262 | 3.155768 |    0.637597 |    2.0 | 3.155768 |
    | 09.01. |    1.0 |       5.876679 | 2.155768 |    0.537739 |    1.0 | 2.155768 |
    | 10.01. |    0.0 |       4.878095 | 1.155768 |     0.43788 |    0.0 | 1.155768 |
    | 11.01. |    0.0 |       3.879512 | 1.155768 |    0.338022 |    0.0 | 1.155768 |
    | 12.01. |    0.0 |       2.880928 | 1.155768 |    0.238164 |    0.0 | 1.155768 |
    | 13.01. |    0.0 |       1.882449 | 1.155647 |    0.138316 |    0.0 | 1.155647 |
    | 14.01. |    0.0 |       0.940746 | 0.908959 |    0.059782 |    0.0 | 0.908959 |
    | 15.01. |    0.0 |       0.400649 | 0.400648 |    0.025166 |    0.0 | 0.400648 |
    | 16.01. |    0.0 |       0.167488 | 0.167488 |    0.010695 |    0.0 | 0.167488 |
    | 17.01. |    0.0 |       0.071178 | 0.071178 |    0.004545 |    0.0 | 0.071178 |
    | 18.01. |    0.0 |        0.03147 |  0.03147 |    0.001826 |    0.0 |  0.03147 |
    | 19.01. |    0.0 |       0.010371 | 0.010371 |     0.00093 |    0.0 | 0.010371 |
    | 20.01. |    0.0 |       0.005282 | 0.005282 |    0.000474 |    0.0 | 0.005282 |

    .. raw:: html

        <a
            href="dam_v006_ex2.html"
            target="_blank"
        >Click here to see the graph</a>

    Considering the number of calls, |dam_v006| is quite efficient, again:

    >>> model.numvars.nmb_calls
    132

    However, when comparing it to the number of calls of |llake_v1|, one
    must take the additional overhead of the integration algorithm and the
    smoothing of the (formerly) discontinuous differential equations
    into account.
"""
# import...
# ...from HydPy
from hydpy.auxs.anntools import ann   # pylint: disable=unused-import
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(modeltools.ELSModel):
    """Version 6 of HydPy-Dam."""
    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        dam_model.Pic_Inflow_V1,
    )
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        dam_model.Fix_Min1_V1,
    )
    PART_ODE_METHODS = (
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_SurfaceArea_V1,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_AllowedDischarge_V1,
        dam_model.Calc_Outflow_V2,
    )
    FULL_ODE_METHODS = (
        dam_model.Update_WaterVolume_V1,
    )
    OUTLET_METHODS = (
        dam_model.Pass_Outflow_V1,
    )
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
