# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Retention basin (RUEC) version of HydPy-Dam.

|dam_v007| is a simple "retention basin" model, like the one selectable
via by the "RUEC" option of LARSIM.  Therefore, it resembles |dam_v006|,
which corresponds to LARSIM's "SEEG" option.  The description of the
(numerical)  implementation differences between |dam_v006| and "SEEG"
also holds for the differences between |dam_v007| and "RUEC".

Integration examples:

    We create the same test set as for application model |dam_v006|,
    including an identical inflow series and an identical relationship
    between stage and volume as well as between flood discharge and stage:

    >>> from hydpy import pub, Node, Element
    >>> pub.timegrids = '01.01.2000', '21.01.2000', '1d'
    >>> from hydpy.models.dam_v007 import *
    >>> parameterstep('1d')
    >>> input_ = Node('input_')
    >>> output = Node('output')
    >>> lake = Element('lake', inlets=input_, outlets=output)
    >>> lake.model = model
    >>> from hydpy import IntegrationTest
    >>> test = IntegrationTest(lake,
    ...                        inits=[(states.watervolume, 0.0)])
    >>> test.dateformat = '%d.%m.'

    >>> watervolume2waterlevel(
    ...     weights_input=1e-6, weights_output=4.e6,
    ...     intercepts_hidden=0.0, intercepts_output=-4e6/2)
    >>> waterlevel2flooddischarge(ann(
    ...     weights_input=1e-6, weights_output=4e7,
    ...     intercepts_hidden=0.0, intercepts_output=-4e7/2))
    >>> catchmentarea(86.4)

    >>> input_.sequences.sim.series = [
    ...     0.0, 1.0, 6.0, 12.0, 10.0, 6.0, 3.0, 2.0, 1.0, 0.0,
    ...     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    In the first example, we set the allowed release to 0 m³/s (which makes
    the values of the two water-related control parameters irrelevant).

    >>> allowedrelease(0.0)
    >>> waterlevelminimumtolerance(0.1)
    >>> waterlevelminimumthreshold(0.0)

    Now only flood discharge (due to an activation of the spillway) can
    occur, and the results are identical with the ones of the first example
    on application mode |dam_v006|:

    >>> test('dam_v007_ex1')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |           0.0 |       0.329814 | 0.329814 |    0.057904 |    1.0 | 0.329814 |
    | 03.01. |    6.0 |           0.0 |       2.370574 | 2.370574 |    0.371486 |    6.0 | 2.370574 |
    | 04.01. |   12.0 |           0.0 |       6.452959 | 6.452959 |    0.850751 |   12.0 | 6.452959 |
    | 05.01. |   10.0 |           0.0 |       8.999753 | 8.999753 |    0.937172 |   10.0 | 8.999753 |
    | 06.01. |    6.0 |           0.0 |       8.257426 | 8.257426 |    0.742131 |    6.0 | 8.257426 |
    | 07.01. |    3.0 |           0.0 |        5.96014 |  5.96014 |    0.486374 |    3.0 |  5.96014 |
    | 08.01. |    2.0 |           0.0 |       3.917326 | 3.917326 |    0.320717 |    2.0 | 3.917326 |
    | 09.01. |    1.0 |           0.0 |       2.477741 | 2.477741 |    0.193041 |    1.0 | 2.477741 |
    | 10.01. |    0.0 |           0.0 |       1.293731 | 1.293731 |    0.081262 |    0.0 | 1.293731 |
    | 11.01. |    0.0 |           0.0 |       0.544608 | 0.544608 |    0.034208 |    0.0 | 0.544608 |
    | 12.01. |    0.0 |           0.0 |       0.227669 | 0.227669 |    0.014537 |    0.0 | 0.227669 |
    | 13.01. |    0.0 |           0.0 |       0.096753 | 0.096753 |    0.006178 |    0.0 | 0.096753 |
    | 14.01. |    0.0 |           0.0 |       0.042778 | 0.042778 |    0.002482 |    0.0 | 0.042778 |
    | 15.01. |    0.0 |           0.0 |       0.017186 | 0.017186 |    0.000997 |    0.0 | 0.017186 |
    | 16.01. |    0.0 |           0.0 |       0.005664 | 0.005664 |    0.000508 |    0.0 | 0.005664 |
    | 17.01. |    0.0 |           0.0 |       0.002884 | 0.002884 |    0.000259 |    0.0 | 0.002884 |
    | 18.01. |    0.0 |           0.0 |       0.001469 | 0.001469 |    0.000132 |    0.0 | 0.001469 |
    | 19.01. |    0.0 |           0.0 |       0.000748 | 0.000748 |    0.000067 |    0.0 | 0.000748 |
    | 20.01. |    0.0 |           0.0 |       0.000381 | 0.000381 |    0.000034 |    0.0 | 0.000381 |

    .. raw:: html

        <iframe
            src="dam_v007_ex1.html"
            width="100%"
            height="600px"
            frameborder=0
        ></iframe>

    In the second example, we introduce a more realistic relationship
    between flood discharge and stage.  Now, the spillway starts to become
    relevant when the water volume exceeds around 1.4 million m³:

    >>> waterlevel2flooddischarge(ann(
    ...     weights_input=10.0, weights_output=50.0,
    ...     intercepts_hidden=-20.0, intercepts_output=0.0))

    The initially available storage volume of about 1.4 million m³ reduces
    the peak flow to 7.3 m³/s:

    >>> test('dam_v007_ex2a')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |
    | 02.01. |    1.0 |           0.0 |            0.0 |      0.0 |      0.0864 |    1.0 |      0.0 |
    | 03.01. |    6.0 |           0.0 |       0.000022 | 0.000022 |    0.604798 |    6.0 | 0.000022 |
    | 04.01. |   12.0 |           0.0 |       0.125869 | 0.125869 |    1.630723 |   12.0 | 0.125869 |
    | 05.01. |   10.0 |           0.0 |       7.337517 | 7.337517 |    1.860762 |   10.0 | 7.337517 |
    | 06.01. |    6.0 |           0.0 |       6.687413 | 6.687413 |    1.801369 |    6.0 | 6.687413 |
    | 07.01. |    3.0 |           0.0 |       3.829425 | 3.829425 |    1.729707 |    3.0 | 3.829425 |
    | 08.01. |    2.0 |           0.0 |       2.462161 | 2.462161 |    1.689776 |    2.0 | 2.462161 |
    | 09.01. |    1.0 |           0.0 |       1.602443 | 1.602443 |    1.637725 |    1.0 | 1.602443 |
    | 10.01. |    0.0 |           0.0 |       0.869271 | 0.869271 |     1.56262 |    0.0 | 0.869271 |
    | 11.01. |    0.0 |           0.0 |       0.498579 | 0.498579 |    1.519543 |    0.0 | 0.498579 |
    | 12.01. |    0.0 |           0.0 |       0.348504 | 0.348504 |    1.489432 |    0.0 | 0.348504 |
    | 13.01. |    0.0 |           0.0 |       0.267917 | 0.267917 |    1.466284 |    0.0 | 0.267917 |
    | 14.01. |    0.0 |           0.0 |       0.217618 | 0.217618 |    1.447482 |    0.0 | 0.217618 |
    | 15.01. |    0.0 |           0.0 |       0.183225 | 0.183225 |    1.431651 |    0.0 | 0.183225 |
    | 16.01. |    0.0 |           0.0 |       0.158219 | 0.158219 |    1.417981 |    0.0 | 0.158219 |
    | 17.01. |    0.0 |           0.0 |       0.139064 | 0.139064 |    1.405966 |    0.0 | 0.139064 |
    | 18.01. |    0.0 |           0.0 |       0.124197 | 0.124197 |    1.395235 |    0.0 | 0.124197 |
    | 19.01. |    0.0 |           0.0 |       0.112196 | 0.112196 |    1.385542 |    0.0 | 0.112196 |
    | 20.01. |    0.0 |           0.0 |       0.102307 | 0.102307 |    1.376702 |    0.0 | 0.102307 |

    .. raw:: html

        <iframe
            src="dam_v007_ex2a.html"
            width="100%"
            height="600px"
            frameborder=0
        ></iframe>

    In the last example, |dam_v007| could not handle a second event following
    the first one similarly well, as the spillway does not release the
    remaining water.  Setting the allowed release to 4 m³/s solves this
    problem and also decreases the amount of water stored during the beginning
    of the event and thus further reduces the peak flow to 4.6 m³/s:

    >>> allowedrelease(4.0)
    >>> waterlevelminimumthreshold(0.1)
    >>> test('dam_v007_ex2b')
    |   date | inflow | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |
    -------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |      0.037088 |            0.0 | 0.037088 |   -0.003204 |    0.0 | 0.037088 |
    | 02.01. |    1.0 |       0.24393 |            0.0 |  0.24393 |     0.06212 |    1.0 |  0.24393 |
    | 03.01. |    6.0 |      3.512924 |       0.000001 | 3.512925 |    0.277003 |    6.0 | 3.512925 |
    | 04.01. |   12.0 |      3.999413 |       0.000827 | 4.000241 |    0.968183 |   12.0 | 4.000241 |
    | 05.01. |   10.0 |           4.0 |        0.05527 |  4.05527 |    1.481807 |   10.0 |  4.05527 |
    | 06.01. |    6.0 |           4.0 |       0.572981 | 4.572981 |    1.605102 |    6.0 | 4.572981 |
    | 07.01. |    3.0 |           4.0 |       0.508315 | 4.508315 |    1.474783 |    3.0 | 4.508315 |
    | 08.01. |    2.0 |           4.0 |       0.117913 | 4.117913 |    1.291796 |    2.0 | 4.117913 |
    | 09.01. |    1.0 |           4.0 |       0.015063 | 4.015063 |    1.031294 |    1.0 | 4.015063 |
    | 10.01. |    0.0 |           4.0 |       0.001601 | 4.001601 |    0.685556 |    0.0 | 4.001601 |
    | 11.01. |    0.0 |      3.999967 |        0.00005 | 4.000018 |    0.339954 |    0.0 | 4.000018 |
    | 12.01. |    0.0 |      3.097067 |       0.000001 | 3.097068 |    0.072368 |    0.0 | 3.097068 |
    | 13.01. |    0.0 |       0.40591 |            0.0 |  0.40591 |    0.037297 |    0.0 |  0.40591 |
    | 14.01. |    0.0 |      0.155222 |            0.0 | 0.155222 |    0.023886 |    0.0 | 0.155222 |
    | 15.01. |    0.0 |      0.096838 |            0.0 | 0.096838 |    0.015519 |    0.0 | 0.096838 |
    | 16.01. |    0.0 |      0.070215 |            0.0 | 0.070216 |    0.009452 |    0.0 | 0.070216 |
    | 17.01. |    0.0 |      0.054858 |            0.0 | 0.054858 |    0.004713 |    0.0 | 0.054858 |
    | 18.01. |    0.0 |      0.045172 |            0.0 | 0.045172 |     0.00081 |    0.0 | 0.045172 |
    | 19.01. |    0.0 |      0.038376 |            0.0 | 0.038376 |   -0.002506 |    0.0 | 0.038376 |
    | 20.01. |    0.0 |      0.033349 |            0.0 | 0.033349 |   -0.005387 |    0.0 | 0.033349 |

    .. raw:: html

        <iframe
            src="dam_v007_ex2b.html"
            width="100%"
            height="600px"
            frameborder=0
        ></iframe>

    The initial and final water volumes shown in the last table are slightly
    negative, which is due to the periods of zero inflow in combination
    with the value of parameter |WaterLevelMinimumTolerance| set to
    0.1 m.  One could avoid such negative values by increasing the value
    of parameter |WaterLevelMinimumThreshold| or decreasing the value of
    parameter |WaterLevelMinimumTolerance|.  Theoretically, one could set
    |WaterLevelMinimumTolerance| to zero, but at the cost of potentially
    increased computation times.
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
    """Version 7 of HydPy-Dam."""
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
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_ActualRelease_V2,
        dam_model.Calc_FloodDischarge_V1,
        dam_model.Calc_Outflow_V1,
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
