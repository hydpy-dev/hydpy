# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Pumping station version of HydPy-Dam.

|dam_pump| is a simple model for modelling pumping stations draining low-land areas.
Users can define a relationship between the highest possible pumping rate and the
difference between current inner and outer water levels (
|WaterLevelDifference2MaxForcedDischarge|).  Actual pumping happens when the inner
water level reaches the given target level (|WaterLevelMaximumThreshold|) as
long as the water level at a remote location does not exceed another defined threshold
(|RemoteWaterLevelMaximumThreshold|).  The latter restriction helps to prevent further
increasing high flow conditions in downstream areas.

Integration tests
=================

.. how_to_understand_integration_tests::

We prepare a simulation period of 20 days:

>>> from hydpy import IntegrationTest, Element, Node, pub, round_
>>> pub.timegrids = "2000-01-01", "2000-01-21", "1d"

Besides the standard inlet and outlet nodes, |dam_pump| requires connections with two
receiver nodes.  One of these nodes should inform about the water level immediately
downstream.  The other one should provide water levels from a "sensible" location where
a certain water level should not be exceeded.  We connect these nodes via the remote
sequences |dam_receivers.OWL| (outer water level) and |dam_receivers.RWL| (remote water
level):

>>> from hydpy.inputs import dam_OWL, dam_RWL
>>> inflow, outflow = Node("inflow"), Node("outflow")
>>> outer, remote = Node("outer", variable=dam_OWL), Node("remote", variable=dam_RWL)
>>> dam = Element("dam", inlets=inflow, outlets=outflow, receivers=(outer, remote))

Next, we prepare a |dam_pump| instance and connect it to the |Element| instance:

>>> from hydpy.models.dam_pump import *
>>> parameterstep()
>>> dam.model = model

Parameterising |dam_pump| works similarly to parameterising other |dam| models.  Please
read the documentation on |dam_v001|, which provides in-depth information and should
help understand the following settings:

>>> surfacearea(1.44)
>>> catchmentarea(86.4)
>>> watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
>>> waterleveldifference2maxforceddischarge(PPoly.from_data(xs=[0.0], ys=[1.0]))
>>> waterlevelmaximumthreshold(1.0)
>>> waterlevelmaximumtolerance(0.1)
>>> remotewaterlevelmaximumthreshold(2.0)
>>> remotewaterlevelmaximumtolerance(0.1)
>>> correctionprecipitation(1.0)
>>> correctionevaporation(1.0)
>>> weightevaporation(0.8)
>>> thresholdevaporation(0.0)
>>> toleranceevaporation(0.001)

Now, we prepare an |IntegrationTest| object and use it for registering zero initial
conditions for all state and log sequences:

>>> test = IntegrationTest(dam)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = factors.waterlevel, factors.outerwaterlevel, factors.remotewaterlevel
>>> test.inits = [(states.watervolume, 0.0),
...               (logs.loggedadjustedevaporation, 0.0),
...               (logs.loggedouterwaterlevel, 0.0),
...               (logs.loggedremotewaterlevel, 0.0)]
>>> test.reset_inits()
>>> conditions = sequences.conditions

We set the time series of precipitation, evaporation, inflow, and the outer water level
to constant values and let the remote water level increase constantly over the entire
simulation period:

>>> inputs.precipitation.series = 2.0
>>> inputs.evaporation.series = 1.0
>>> inflow.sequences.sim.series = 2.0
>>> outer.sequences.sim.series = 0.0
>>> remote.sequences.sim.series = numpy.linspace(0.0, 3.0, 20)

.. _dam_pump_drainage:

drainage
________

The following test run shows that the pumping starts when the inner water level reaches
the defined threshold of 1 m.  The outflow gradually becomes closer to the constant
inflow until the remote water level reaches the other defined threshold of 2 m:

.. integration-test::

    >>> test("dam_pump_drainage")
    |   date | precipitation | evaporation | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | adjustedprecipitation | adjustedevaporation | actualevaporation | inflow | maxforceddischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |           2.0 |         1.0 |   0.174816 |             0.0 |              0.0 |             0.175104 |              0.033333 |            0.013333 |              0.01 |    2.0 |                1.0 |             0.0 |      0.0 |    0.174816 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |           2.0 |         1.0 |   0.349114 |             0.0 |              0.0 |             0.349114 |              0.033333 |               0.016 |             0.016 |    2.0 |                1.0 |             0.0 |      0.0 |    0.349114 |    2.0 |   0.0 |      0.0 | 0.157895 |
    | 03.01. |           2.0 |         1.0 |   0.523365 |             0.0 |         0.157895 |             0.523365 |              0.033333 |            0.016533 |          0.016533 |    2.0 |                1.0 |             0.0 |      0.0 |    0.523365 |    2.0 |   0.0 |      0.0 | 0.315789 |
    | 04.01. |           2.0 |         1.0 |   0.697607 |             0.0 |         0.315789 |             0.697607 |              0.033333 |             0.01664 |           0.01664 |    2.0 |                1.0 |             0.0 |      0.0 |    0.697607 |    2.0 |   0.0 |      0.0 | 0.473684 |
    | 05.01. |           2.0 |         1.0 |   0.871728 |             0.0 |         0.473684 |             0.871848 |              0.033333 |            0.016661 |          0.016661 |    2.0 |                1.0 |        0.001382 | 0.001382 |    0.871728 |    2.0 |   0.0 | 0.001382 | 0.631579 |
    | 06.01. |           2.0 |         1.0 |   1.025317 |             0.0 |         0.631579 |             1.025227 |              0.033333 |            0.016666 |          0.016666 |    2.0 |                1.0 |        0.239024 | 0.239024 |    1.025317 |    2.0 |   0.0 | 0.239024 | 0.789474 |
    | 07.01. |           2.0 |         1.0 |   1.118209 |             0.0 |         0.789474 |             1.118263 |              0.033333 |            0.016666 |          0.016666 |    2.0 |                1.0 |        0.941528 | 0.941528 |    1.118209 |    2.0 |   0.0 | 0.941528 | 0.947368 |
    | 08.01. |           2.0 |         1.0 |    1.20624 |             0.0 |         0.947368 |             1.206425 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.997784 | 0.997784 |     1.20624 |    2.0 |   0.0 | 0.997784 | 1.105263 |
    | 09.01. |           2.0 |         1.0 |   1.294084 |             0.0 |         1.105263 |             1.294087 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.999961 | 0.999961 |    1.294084 |    2.0 |   0.0 | 0.999961 | 1.263158 |
    | 10.01. |           2.0 |         1.0 |   1.381924 |             0.0 |         1.263158 |             1.381924 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.999999 | 0.999999 |    1.381924 |    2.0 |   0.0 | 0.999999 | 1.421053 |
    | 11.01. |           2.0 |         1.0 |   1.469764 |             0.0 |         1.421053 |             1.469764 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |             1.0 |      1.0 |    1.469764 |    2.0 |   0.0 |      1.0 | 1.578947 |
    | 12.01. |           2.0 |         1.0 |   1.557604 |             0.0 |         1.578947 |             1.557604 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |             1.0 |      1.0 |    1.557604 |    2.0 |   0.0 |      1.0 | 1.736842 |
    | 13.01. |           2.0 |         1.0 |   1.645444 |             0.0 |         1.736842 |             1.645444 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.999994 | 0.999994 |    1.645444 |    2.0 |   0.0 | 0.999994 | 1.894737 |
    | 14.01. |           2.0 |         1.0 |   1.733964 |             0.0 |         1.894737 |             1.733964 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.992131 | 0.992131 |    1.733964 |    2.0 |   0.0 | 0.992131 | 2.052632 |
    | 15.01. |           2.0 |         1.0 |   1.901139 |             0.0 |         2.052632 |             1.901139 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.081774 | 0.081774 |    1.901139 |    2.0 |   0.0 | 0.081774 | 2.210526 |
    | 16.01. |           2.0 |         1.0 |   2.075373 |             0.0 |         2.210526 |             2.075373 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.000063 | 0.000063 |    2.075373 |    2.0 |   0.0 | 0.000063 | 2.368421 |
    | 17.01. |           2.0 |         1.0 |   2.249613 |             0.0 |         2.368421 |             2.249613 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.249613 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |           2.0 |         1.0 |   2.423853 |             0.0 |         2.526316 |             2.423853 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.423853 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |           2.0 |         1.0 |   2.598093 |             0.0 |         2.684211 |             2.598093 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.598093 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |           2.0 |         1.0 |   2.772333 |             0.0 |         2.842105 |             2.772333 |              0.033333 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.772333 |    2.0 |   0.0 |      0.0 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
import hydpy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import

from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core.typingtools import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(modeltools.ELSModel):
    """Pumping station version of HydPy-Dam."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (dam_model.Calc_AdjustedEvaporation_V1,)
    RECEIVER_METHODS = (
        dam_model.Pick_LoggedOuterWaterLevel_V1,
        dam_model.Pick_LoggedRemoteWaterLevel_V1,
    )
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        dam_model.Calc_AdjustedPrecipitation_V1,
        dam_model.Pic_Inflow_V1,
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_OuterWaterLevel_V1,
        dam_model.Calc_RemoteWaterLevel_V1,
        dam_model.Calc_WaterLevelDifference_V1,
        dam_model.Calc_MaxForcedDischarge_V1,
        dam_model.Calc_ForcedDischarge_V1,
        dam_model.Calc_ActualEvaporation_V1,
        dam_model.Calc_Outflow_V3,
    )
    FULL_ODE_METHODS = (dam_model.Update_WaterVolume_V1,)
    OUTLET_METHODS = (
        dam_model.Calc_WaterLevel_V1,
        dam_model.Calc_OuterWaterLevel_V1,
        dam_model.Calc_RemoteWaterLevel_V1,
        dam_model.Pass_Outflow_V1,
    )
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    def check_waterbalance(
        self,
        initial_conditions: Dict[str, Dict[str, ArrayFloat]],
    ) -> float:
        r"""Determine the water balance error of the previous simulation run in million
        m³.

        Method |Model.check_waterbalance| calculates the balance error as follows:

        :math:`Seconds \cdot 10^{-6} \cdot \sum_{t=t0}^{t1}
        \big( AdjustedPrecipitation_t - ActualEvaporation_t + Inflow_t - Outflow_t \big)
        + \big( WaterVolume_{t0}^k - WaterVolume_{t1}^k \big)`

        The returned error should always be in scale with numerical precision so
        that it does not affect the simulation results in any relevant manner.

        Pick the required initial conditions before starting the simulation via
        property |Sequences.conditions|.  See the integration tests of the application
        model |dam_v001| for some examples.
        """
        fluxes = self.sequences.fluxes
        first = initial_conditions["states"]
        last = self.sequences.states
        return (hydpy.pub.timegrids.stepsize.seconds / 1e6) * (
            sum(fluxes.adjustedprecipitation.series)
            - sum(fluxes.actualevaporation.series)
            + sum(fluxes.inflow.series)
            - sum(fluxes.outflow.series)
        ) - (last.watervolume - first["watervolume"])


tester = Tester()
cythonizer = Cythonizer()
