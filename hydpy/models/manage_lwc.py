# pylint: disable=line-too-long, unused-wildcard-import
"""

Integration tests
=================

.. how_to_understand_integration_tests::


>>> from hydpy import pub
>>> pub.timegrids = "2000-01-01", "2000-03-01", "1d"

>>> from hydpy import Element, FusedVariable, Node, Nodes
>>> from hydpy.aliases import dam_observers_R, dam_states_WaterVolume, manage_senders_Request
>>> t = Node("t")
>>> r_1, r_1a, r_2, r_2a, r_2b, r_2b1 = Nodes(
...     "r_1", "r_1a", "r_2", "r_2a", "r_2b", "r_2b1",
...     defaultvariable=FusedVariable("R", dam_observers_R, manage_senders_Request),
... )
>>> v_1, v_1a, v_2, v_2a, v_2b, v_2b1 = Nodes(
...     "v_1", "v_1a", "v_2", "v_2a", "v_2b", "v_2b1",
...     defaultvariable=dam_states_WaterVolume,
... )
>>> d_1 = Element("d_1", inlets="q_1a_1", outlets=t, observers=r_1, outputs=v_1)
>>> d_1a = Element("d_1a", outlets="q_1a_1", observers=r_1a, outputs=v_1a)
>>> d_2 = Element("d_2", inlets=("q_2a_2", "q_2b_2"), outlets=t, observers=r_2, outputs=v_2)
>>> d_2a = Element("d_2a", outlets="q_2a_2", observers=r_2a, outputs=v_2a)
>>> d_2b = Element("d_2b", inlets="q_2b1_2b", outlets="q_2b_2", observers=r_2b, outputs=v_2b)
>>> d_2b1 = Element("d_2b1", outlets="q_2b1_2b", observers=r_2b1, outputs=v_2b1)
>>> dams = d_1, d_1a, d_2, d_2a, d_2b, d_2b1

>>> lwc = Element(
...     "lwc",
...     receivers=[t, v_1, v_1a, v_2, v_2a, v_2b, v_2b1],
...     senders=[r_1, r_1a, r_2, r_2a, r_2b, r_2b1],
... )

>>> from hydpy import PPoly, prepare_model
>>> from numpy import inf
>>> for dam in dams:
...     dam.model = prepare_model("dam_llake")
...     control = dam.model.parameters.control
...     control.catchmentarea(86.4)
...     control.surfacearea(1.44)
...     control.correctionprecipitation(1.2)
...     control.correctionevaporation(1.2)
...     control.weightevaporation(0.8)
...     control.thresholdevaporation(0.0)
...     control.dischargetolerance(0.1)
...     control.toleranceevaporation(0.001)
...     control.allowedwaterleveldrop(inf)
...     control.watervolume2waterlevel(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
...     control.waterlevel2flooddischarge(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 0.1]))
...     control.commission(0)
...     control.pars.update()

>>> from hydpy.models.manage_lwc import *
>>> parameterstep()
>>> nmbsources(6)
>>> active(d_1=True, d_1a=True, d_2=True, d_2a=True, d_2b=True, d_2b1=True)
>>> volumemin(d_1=0.0, d_1a=0.0, d_2=0.0, d_2a=0.0, d_2b=0.0, d_2b1=0.0)
>>> volumemax(d_1=1.0, d_1a=1.0, d_2=1.0, d_2a=1.0, d_2b=1.0, d_2b1=1.0)
>>> releasemax(d_1=0.5, d_1a=0.5, d_2=0.5, d_2a=0.5, d_2b=0.5, d_2b1=0.5)
>>> demand(1.0)
>>> lwc.model = model

>>> def calculate_demand(model) -> None:
...     con = model.parameters.control.fastaccess
...     flu = model.sequences.fluxes.fastaccess
...     log = model.sequences.logs.fastaccess
...     q0: float = 1.0
...     q1: float = 1.1
...     q: float = log.loggeddischarge
...     con.demand = q0 * min(max(1.0 - (q - q0) / (q1 - q0), 0.0), 1.0)
>>> demand(callback=calculate_demand)

>>> from hydpy.core.testtools import IntegrationTest
>>> test = IntegrationTest(lwc)


>>> inits = [(logs.loggedwatervolume, 1.0), (logs.loggeddischarge, 2.0)]
>>> for dam in dams:
...     inits.append((dam.model.sequences.states.watervolume, 1.0))
...     inits.append((dam.model.sequences.logs.loggedadjustedevaporation, 0.0))
>>> test.inits = inits

.. _manage_lwc_base_scenario:

base scenario
_____________


.. integration-test::

    >>> test("manage_lwc_base_scenario")
    |                date |   demand |       request | inflow1 | inflow2 | outflow1 | outflow2 | required1 | required2 |   target | volume1 |  volume2 |
    ----------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-09-01 00:00:00 |      0.0 | nan       nan |     0.0 |     0.0 |      nan |      nan |       nan |       nan | 1.836738 |     0.0 | 0.841306 |
    | 2000-09-02 00:00:00 |      0.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 | 1.545259 |     0.0 | 0.707795 |
    | 2000-09-03 00:00:00 |      0.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 | 1.300035 |     0.0 | 0.595472 |
    | 2000-09-04 00:00:00 |      0.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 | 1.093727 |     0.0 | 0.500974 |
    | 2000-09-05 00:00:00 |  0.06273 | 0.0   0.06273 |     0.0 |     0.0 |      nan |      nan |       0.0 |   0.06273 | 0.920159 |     0.0 | 0.421473 |
    | 2000-09-06 00:00:00 |      1.0 | 0.0       1.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       1.0 | 1.001317 |     0.0 | 0.334959 |
    | 2000-09-07 00:00:00 | 0.986826 | 0.0  0.986826 |     0.0 |     0.0 |      nan |      nan |       0.0 |  0.986826 | 0.986919 |     0.0 | 0.249689 |
    | 2000-09-08 00:00:00 |      1.0 | 0.0       1.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       1.0 | 1.000004 |     0.0 | 0.163289 |
    | 2000-09-09 00:00:00 | 0.999959 | 0.0  0.999959 |     0.0 |     0.0 |      nan |      nan |       0.0 |  0.999959 | 0.999959 |     0.0 | 0.076892 |
    | 2000-09-10 00:00:00 |      1.0 | 0.0  0.889957 |     0.0 |     0.0 |      nan |      nan |       0.0 |  0.889957 | 0.889957 |     0.0 |      0.0 |
    | 2000-09-11 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-12 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-13 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-14 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-15 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-16 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-17 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-18 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-19 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-20 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-21 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-22 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-23 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-24 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-25 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-26 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-27 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-28 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-29 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |
    | 2000-09-30 00:00:00 |      1.0 | 0.0       0.0 |     0.0 |     0.0 |      nan |      nan |       0.0 |       0.0 |      0.0 |     0.0 |      0.0 |

"""
from hydpy.core.objecttools import devicename
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import devicetools
from hydpy.core import modeltools
from hydpy.core.typingtools import *

# ...from manage
from hydpy.models.manage import manage_model


class Model(modeltools.AdHocModel):
    """|manage_lwc.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Manage-LWC", description="low water control management model"
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = (
        manage_model.Pick_LoggedDischarge_V1,
        manage_model.Pick_LoggedWaterVolume_V1,
    )
    RUN_METHODS = (manage_model.Calc_Demand_V1, manage_model.Calc_Request_V1)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = (manage_model.Pass_Request_V1,)
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    sourcenames: list[str]

    def __init__(self) -> None:
        super().__init__()
        self.sourcenames = []

    def _connect_receivers(self) -> None:
        """

        >>> from hydpy import Element, Nodes
        >>> volumes = Nodes("volume1", "volume2", defaultvariable="WaterVolumes")
        >>> lwc = Element(
        ...     "lwc",
        ...     # observers="gauge",
        ...     receivers=volumes,
        ...     # senders=["release1", "release2"],
        ... )
        >>> from hydpy.models.manage_lwc import *
        >>> parameterstep()
        >>> lwc.model = model
        """

        name2elements = devicetools._registry[devicetools.Element]

        volume_nodes = []
        for sourcename in self.sourcenames:
            element = name2elements[sourcename]
            # ToDo: also search in senders...?
            selected = [n for n in element.outputs if n in self.element.receivers]
            assert len(selected) == 1
            volume_nodes.append(selected[0])
        self.sequences.receivers.watervolume.connect_to_nodes(
            group="receivers",
            available_nodes=volume_nodes,
            applied_nodes=[],
            report_noconnect=True,
        )

        target_nodes = [n for n in self.element.receivers if str(n.variable) == "Q"]
        assert len(target_nodes) == 1
        self.sequences.receivers.q.connect_to_nodes(
            group="receivers",
            available_nodes=target_nodes,
            applied_nodes=[],
            report_noconnect=True,
        )

    def _connect_senders(self) -> None:
        """Todo"""

        name2elements = devicetools._registry[devicetools.Element]

        request_nodes = []
        for sourcename in self.sourcenames:
            element = name2elements[sourcename]
            # ToDo: also search in inputs...?
            selected = [n for n in element.observers if n in self.element.senders]
            assert len(selected) == 1
            request_nodes.append(selected[0])
        self.sequences.senders.request.connect_to_nodes(
            group="senders",
            available_nodes=request_nodes,
            applied_nodes=[],
            report_noconnect=True,
        )


tester = Tester()
cythonizer = Cythonizer()
