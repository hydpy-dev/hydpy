"""
The |sw1d.DOCNAME.long| model family member |sw1d_storage| is a storage submodel for
keeping track of the water amount stored in a channel segment and calculating the water
level.

Please refer to the documentation of the "user model" |sw1d_channel| and the
"composite model" |sw1d_network|, where we demonstrate and discuss |sw1d_storage| in
detail.
"""

# pylint: disable=unused-wildcard-import
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import routinginterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(sw1d_model.Main_CrossSectionModel_V2, routinginterfaces.StorageModel_V1):
    """|sw1d_storage.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="SW1D-Storage",
        description="submodel for calculating a single channel segment's water balance",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = (
        sw1d_model.Pick_LateralFlow_V1,
        sw1d_model.Calc_WaterDepth_WaterLevel_V1,
    )
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        sw1d_model.Update_Storage_V1,
        sw1d_model.Get_WaterVolume_V1,
        sw1d_model.Get_WaterLevel_V1,
        sw1d_model.Set_TimeStep_V1,
    )
    ADD_METHODS = (
        sw1d_model.Calc_NetInflow_V1,
        sw1d_model.Update_WaterVolume_V1,
        sw1d_model.Calc_WaterDepth_WaterLevel_CrossSectionModel_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = (sw1d_model.Pass_WaterLevel_V1,)
    SUBMODELINTERFACES = (
        routinginterfaces.CrossSectionModel_V2,
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.RoutingModel_V3,
        routinginterfaces.StorageModel_V1,
    )
    SUBMODELS = ()

    crosssection = modeltools.SubmodelProperty(routinginterfaces.CrossSectionModel_V2)

    routingmodelsupstream = modeltools.SubmodelsProperty(
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.RoutingModel_V3,
        sidemodels=True,
    )
    routingmodelsdownstream = modeltools.SubmodelsProperty(
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.RoutingModel_V3,
        sidemodels=True,
    )


tester = Tester()
cythonizer = Cythonizer()
