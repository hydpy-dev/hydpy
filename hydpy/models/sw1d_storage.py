# -*- coding: utf-8 -*-
"""
The *HydPy-SW1D* model family member |sw1d_storage| is a storage submodel for keeping
track of the water amount stored in a channel segment and calculating the water level.

Please refer to the documentation of the "user model" |sw1d_channel| and the
"composite model" |sw1d_network|, where we demonstrate and discuss |sw1d_storage| in
detail.
"""
# pylint: disable=unused-wildcard-import
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import channelinterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(modeltools.AdHocModel, channelinterfaces.StorageModel_V1):
    """A storage submodel for calculating a single channel segment's water balance and
    water level."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        sw1d_model.Perform_Preprocessing_V3,
        sw1d_model.Update_Storage_V1,
        sw1d_model.Perform_Postprocessing_V3,
        sw1d_model.Get_WaterVolume_V1,
        sw1d_model.Get_WaterLevel_V1,
        sw1d_model.Set_TimeStep_V1,
    )
    ADD_METHODS = (
        sw1d_model.Pick_LateralFlow_V1,
        sw1d_model.Calc_WaterDepth_V1,
        sw1d_model.Calc_WaterLevel_V1,
        sw1d_model.Calc_NetInflow_V1,
        sw1d_model.Update_WaterVolume_V1,
        sw1d_model.Pass_WaterLevel_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        channelinterfaces.StorageModel_V1,
    )
    SUBMODELS = ()

    routingmodelsupstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        sidemodels=True,
    )
    routingmodelsdownstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        sidemodels=True,
    )


tester = Tester()
cythonizer = Cythonizer()
