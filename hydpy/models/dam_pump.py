# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Pumping station version of HydPy-Dam.

|dam_pump| is a simple model for modelling pumping stations draining low-land areas.
Users can define a relationship between the highest possible pumping rate and the
difference between current inner and outer water levels
(|WaterLevelDifference2MaxForcedDischarge|).  Actual pumping happens when the inner
water level reaches the given target level (|WaterLevelMaximumThreshold|) as
long as the water level at a remote location does not exceed another defined threshold
(|RemoteWaterLevelMaximumThreshold|).  The latter restriction helps to prevent further
increasing high flow conditions in downstream areas. If the |MaxForcedDischarge| is
negative, the pumping process is carried out in the reverse direction (e.g. for
modelling irrigation processes).

By default, |dam_pump| neither takes precipitation nor evaporation into account, but
you can add submodels that comply with the |PrecipModel_V2| or |PETModel_V1| interface
that supply this information.

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

>>> from hydpy.aliases import dam_receivers_OWL, dam_receivers_RWL
>>> inflow = Node("inflow")
>>> outflow = Node("outflow")
>>> outer = Node("outer", variable=dam_receivers_OWL)
>>> remote = Node("remote", variable=dam_receivers_RWL)
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

We add |meteo_precip_io| and |evap_io| submodels that can supply predefined time series
of precipitation and potential evaporation:

>>> with model.add_precipmodel_v2("meteo_precip_io"):
...     precipitationfactor(1.0)
>>> with model.add_pemodel_v1("evap_io"):
...     evapotranspirationfactor(1.0)

Now, we prepare an |IntegrationTest| object and register zero initial conditions for
all state and log sequences:

>>> test = IntegrationTest(dam)
>>> test.dateformat = "%d.%m."
>>> test.plotting_options.axis1 = fluxes.inflow, fluxes.outflow
>>> test.plotting_options.axis2 = factors.waterlevel, factors.outerwaterlevel, factors.remotewaterlevel
>>> test.inits = [(states.watervolume, 0.0),
...               (logs.loggedadjustedevaporation, 0.0),
...               (logs.loggedouterwaterlevel, 0.0),
...               (logs.loggedremotewaterlevel, 0.0)]
>>> test.reset_inits()
>>> conditions = model.conditions

We set the time series of precipitation, evaporation, inflow, and the outer water level
to constant values and let the remote water level increase constantly over the entire
simulation period:

>>> model.precipmodel.sequences.inputs.precipitation.series = 2.0
>>> model.pemodel.sequences.inputs.referenceevapotranspiration.series = 1.0
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
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | maxforceddischarge | forceddischarge |  outflow | watervolume | inflow | outer |  outflow |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.174533 |             0.0 |              0.0 |             0.174533 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.013278 |    2.0 |                1.0 |             0.0 |      0.0 |    0.174533 |    2.0 |   0.0 |      0.0 |      0.0 |
    | 02.01. |    0.34883 |             0.0 |              0.0 |              0.34883 |           2.0 |              0.033333 |                  1.0 |               0.016 |             0.016 |    2.0 |                1.0 |             0.0 |      0.0 |     0.34883 |    2.0 |   0.0 |      0.0 | 0.157895 |
    | 03.01. |   0.523082 |             0.0 |         0.157895 |             0.523082 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    2.0 |                1.0 |             0.0 |      0.0 |    0.523082 |    2.0 |   0.0 |      0.0 | 0.315789 |
    | 04.01. |   0.697324 |             0.0 |         0.315789 |             0.697324 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    2.0 |                1.0 |             0.0 |      0.0 |    0.697324 |    2.0 |   0.0 |      0.0 | 0.473684 |
    | 05.01. |   0.871535 |             0.0 |         0.473684 |             0.871534 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    2.0 |                1.0 |        0.000342 | 0.000342 |    0.871535 |    2.0 |   0.0 | 0.000342 | 0.631579 |
    | 06.01. |   1.025268 |             0.0 |         0.631579 |             1.025276 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |                1.0 |        0.237348 | 0.237348 |    1.025268 |    2.0 |   0.0 | 0.237348 | 0.789474 |
    | 07.01. |   1.118228 |             0.0 |         0.789474 |             1.118229 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |                1.0 |         0.94074 |  0.94074 |    1.118228 |    2.0 |   0.0 |  0.94074 | 0.947368 |
    | 08.01. |    1.20616 |             0.0 |         0.947368 |             1.206165 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.998939 | 0.998939 |     1.20616 |    2.0 |   0.0 | 0.998939 | 1.105263 |
    | 09.01. |   1.294004 |             0.0 |         1.105263 |             1.294007 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.999961 | 0.999961 |    1.294004 |    2.0 |   0.0 | 0.999961 | 1.263158 |
    | 10.01. |   1.381844 |             0.0 |         1.263158 |             1.381844 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.999999 | 0.999999 |    1.381844 |    2.0 |   0.0 | 0.999999 | 1.421053 |
    | 11.01. |   1.469684 |             0.0 |         1.421053 |             1.469684 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |             1.0 |      1.0 |    1.469684 |    2.0 |   0.0 |      1.0 | 1.578947 |
    | 12.01. |   1.557524 |             0.0 |         1.578947 |             1.557524 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |             1.0 |      1.0 |    1.557524 |    2.0 |   0.0 |      1.0 | 1.736842 |
    | 13.01. |   1.645364 |             0.0 |         1.736842 |             1.645364 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.999994 | 0.999994 |    1.645364 |    2.0 |   0.0 | 0.999994 | 1.894737 |
    | 14.01. |   1.733884 |             0.0 |         1.894737 |             1.733884 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.992131 | 0.992131 |    1.733884 |    2.0 |   0.0 | 0.992131 | 2.052632 |
    | 15.01. |   1.901059 |             0.0 |         2.052632 |             1.901059 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.081774 | 0.081774 |    1.901059 |    2.0 |   0.0 | 0.081774 | 2.210526 |
    | 16.01. |   2.075293 |             0.0 |         2.210526 |             2.075293 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |        0.000063 | 0.000063 |    2.075293 |    2.0 |   0.0 | 0.000063 | 2.368421 |
    | 17.01. |   2.249533 |             0.0 |         2.368421 |             2.249533 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.249533 |    2.0 |   0.0 |      0.0 | 2.526316 |
    | 18.01. |   2.423773 |             0.0 |         2.526316 |             2.423773 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.423773 |    2.0 |   0.0 |      0.0 | 2.684211 |
    | 19.01. |   2.598013 |             0.0 |         2.684211 |             2.598013 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.598013 |    2.0 |   0.0 |      0.0 | 2.842105 |
    | 20.01. |   2.772253 |             0.0 |         2.842105 |             2.772253 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |                1.0 |             0.0 |      0.0 |    2.772253 |    2.0 |   0.0 |      0.0 |      3.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0

.. _dam_pump_irrigation:

irrigation
__________

The following test run shows that the pumping (in reversed direction) starts when
the inner water level is lower than the defined threshold of 1 m and the remote
water level is above the defined threshold of 2 m. When the water level rises
above 1 meter, the pumping rate quickly decreases to 0.

>>> waterleveldifference2maxforceddischarge(PPoly.from_data(xs=[0.0], ys=[-1.0]))
>>> remote.sequences.sim.series = numpy.linspace(1.0, 4.0, 20)
>>> waterlevelmaximumthreshold(2.0)

.. integration-test::

    >>> test("dam_pump_irrigation")
    |   date | waterlevel | outerwaterlevel | remotewaterlevel | waterleveldifference | precipitation | adjustedprecipitation | potentialevaporation | adjustedevaporation | actualevaporation | inflow | maxforceddischarge | forceddischarge |   outflow | watervolume | inflow | outer |   outflow |   remote |
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |   0.174533 |             0.0 |              0.0 |             0.174533 |           2.0 |              0.033333 |                  1.0 |            0.013333 |          0.013278 |    2.0 |               -1.0 |             0.0 |       0.0 |    0.174533 |    2.0 |   0.0 |       0.0 |      1.0 |
    | 02.01. |    0.34883 |             0.0 |              1.0 |              0.34883 |           2.0 |              0.033333 |                  1.0 |               0.016 |             0.016 |    2.0 |               -1.0 |             0.0 |       0.0 |     0.34883 |    2.0 |   0.0 |       0.0 | 1.157895 |
    | 03.01. |   0.523082 |             0.0 |         1.157895 |             0.523082 |           2.0 |              0.033333 |                  1.0 |            0.016533 |          0.016533 |    2.0 |               -1.0 |             0.0 |       0.0 |    0.523082 |    2.0 |   0.0 |       0.0 | 1.315789 |
    | 04.01. |   0.697324 |             0.0 |         1.315789 |             0.697324 |           2.0 |              0.033333 |                  1.0 |             0.01664 |           0.01664 |    2.0 |               -1.0 |             0.0 |       0.0 |    0.697324 |    2.0 |   0.0 |       0.0 | 1.473684 |
    | 05.01. |   0.871565 |             0.0 |         1.473684 |             0.871565 |           2.0 |              0.033333 |                  1.0 |            0.016661 |          0.016661 |    2.0 |               -1.0 |             0.0 |       0.0 |    0.871565 |    2.0 |   0.0 |       0.0 | 1.631579 |
    | 06.01. |   1.045805 |             0.0 |         1.631579 |             1.045805 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |               -1.0 |             0.0 |       0.0 |    1.045805 |    2.0 |   0.0 |       0.0 | 1.789474 |
    | 07.01. |    1.22005 |             0.0 |         1.789474 |              1.22005 |           2.0 |              0.033333 |                  1.0 |            0.016666 |          0.016666 |    2.0 |               -1.0 |       -0.000063 | -0.000063 |     1.22005 |    2.0 |   0.0 | -0.000063 | 1.947368 |
    | 08.01. |   1.401356 |             0.0 |         1.947368 |             1.401356 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |       -0.081774 | -0.081774 |    1.401356 |    2.0 |   0.0 | -0.081774 | 2.105263 |
    | 09.01. |   1.661316 |             0.0 |         2.105263 |             1.661316 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |       -0.992131 | -0.992131 |    1.661316 |    2.0 |   0.0 | -0.992131 | 2.263158 |
    | 10.01. |   1.921758 |             0.0 |         2.263158 |             1.921753 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |       -0.997715 | -0.997715 |    1.921758 |    2.0 |   0.0 | -0.997715 | 2.421053 |
    | 11.01. |    2.12494 |             0.0 |         2.421053 |             2.124942 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |       -0.334972 | -0.334972 |     2.12494 |    2.0 |   0.0 | -0.334972 | 2.578947 |
    | 12.01. |   2.299214 |             0.0 |         2.578947 |             2.299216 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |       -0.000401 | -0.000401 |    2.299214 |    2.0 |   0.0 | -0.000401 | 2.736842 |
    | 13.01. |   2.473454 |             0.0 |         2.736842 |             2.473455 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |       -0.000001 | -0.000001 |    2.473454 |    2.0 |   0.0 | -0.000001 | 2.894737 |
    | 14.01. |   2.647694 |             0.0 |         2.894737 |             2.647694 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |             0.0 |       0.0 |    2.647694 |    2.0 |   0.0 |       0.0 | 3.052632 |
    | 15.01. |   2.821934 |             0.0 |         3.052632 |             2.821934 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |             0.0 |       0.0 |    2.821934 |    2.0 |   0.0 |       0.0 | 3.210526 |
    | 16.01. |   2.996174 |             0.0 |         3.210526 |             2.996174 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |             0.0 |       0.0 |    2.996174 |    2.0 |   0.0 |       0.0 | 3.368421 |
    | 17.01. |   3.170414 |             0.0 |         3.368421 |             3.170414 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |             0.0 |       0.0 |    3.170414 |    2.0 |   0.0 |       0.0 | 3.526316 |
    | 18.01. |   3.344654 |             0.0 |         3.526316 |             3.344654 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |             0.0 |       0.0 |    3.344654 |    2.0 |   0.0 |       0.0 | 3.684211 |
    | 19.01. |   3.518894 |             0.0 |         3.684211 |             3.518894 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |             0.0 |       0.0 |    3.518894 |    2.0 |   0.0 |       0.0 | 3.842105 |
    | 20.01. |   3.693134 |             0.0 |         3.842105 |             3.693134 |           2.0 |              0.033333 |                  1.0 |            0.016667 |          0.016667 |    2.0 |               -1.0 |             0.0 |       0.0 |    3.693134 |    2.0 |   0.0 |       0.0 |      4.0 |

There is no indication of an error in the water balance:

>>> round_(model.check_waterbalance(conditions))
0.0
"""
# import...
# ...from HydPy
import hydpy
from hydpy.auxs.anntools import ANN  # pylint: disable=unused-import
from hydpy.auxs.ppolytools import Poly, PPoly  # pylint: disable=unused-import
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.exe.modelimports import *

# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_solver


class Model(dam_model.Main_PrecipModel_V2, dam_model.Main_PEModel_V1):
    """Pumping station version of HydPy-Dam."""

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        dam_model.Calc_Precipitation_V1,
        dam_model.Calc_PotentialEvaporation_V1,
        dam_model.Calc_AdjustedEvaporation_V1,
    )
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
    SUBMODELINTERFACES = (precipinterfaces.PrecipModel_V2, petinterfaces.PETModel_V1)
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)

    def check_waterbalance(self, initial_conditions: ConditionsModel) -> float:
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
        first = initial_conditions["model"]["states"]
        last = self.sequences.states
        return (hydpy.pub.timegrids.stepsize.seconds / 1e6) * (
            sum(fluxes.adjustedprecipitation.series)
            - sum(fluxes.actualevaporation.series)
            + sum(fluxes.inflow.series)
            - sum(fluxes.outflow.series)
        ) - (last.watervolume - first["watervolume"])


tester = Tester()
cythonizer = Cythonizer()
