# -*- coding: utf-8 -*-
"""Calculate runoff concentration with linear storage cascade model ("Nash cascade").

|rconc_nash| is a submodel that supports its main model by calculating the runoff
concentration using the storage cascade approach.

See the integration tests of the application model |hland_v3|, which use |rconc_nash|
as a submodel.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.interfaces import rconcinterfaces
from hydpy.models.rconc import rconc_model
from hydpy.core.typingtools import *


class Model(rconc_model.Sub_RConcModel, rconcinterfaces.RConcModel_V1):
    """A model that calculates runoff concentration using the storage cascade
    approach."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        rconc_model.Set_Inflow_V1,
        rconc_model.Determine_Outflow_V2,
        rconc_model.Get_Outflow_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Return the water balance after the submodel has been executed."""

        waterbalance = self.sequences.states.sc - initial_conditions["states"]["sc"]

        return float(numpy.sum(waterbalance))


tester = Tester()
cythonizer = Cythonizer()
