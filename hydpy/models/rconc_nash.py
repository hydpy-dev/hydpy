# -*- coding: utf-8 -*-
"""Calculate runoff concentration by linear storage cascade model ('Nash cascade').

|rconc_nash| is a submodel that supplies its main model with the
calculation of the runoff concentration by the storage cascade approach.

The integration test of the application model |hland_v3| uses the
|rconc_nash| submodel.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.interfaces import rconcinterfaces
from hydpy.models.rconc import rconc_model


class Model(rconc_model.Sub_RConcModel, rconcinterfaces.RConcModel_V1):
    """Model that calculates runoff concentration by storage cascade approach"""

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


tester = Tester()
cythonizer = Cythonizer()
