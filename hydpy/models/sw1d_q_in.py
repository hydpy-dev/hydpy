# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""
The *HydPy-SW1D* model family member |sw1d_q_in| is a simple routing submodel, which
allows taking observed or previously simulated discharge series as "longitudinal"
channel inflow.

Please refer to the documentation of the "user model" |sw1d_channel| and the
"composite model" |sw1d_network|, where we demonstrate and discuss |sw1d_q_in| in more
detail (see, for example, `:ref:`sw1d_channel_longitudinal_inflow`).
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import channelinterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(modeltools.AdHocModel, channelinterfaces.RoutingModel_V1):
    """A simple routing submodel for inserting "longitudinal" inflow into the first
    segment of a channel."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        sw1d_model.Perform_Preprocessing_V1,
        sw1d_model.Determine_MaxTimeStep_V2,
        sw1d_model.Determine_Discharge_V2,
        sw1d_model.Perform_Postprocessing_V1,
        sw1d_model.Get_MaxTimeStep_V1,
        sw1d_model.Get_Discharge_V1,
        sw1d_model.Get_PartialDischargeUpstream_V1,
        sw1d_model.Get_DischargeVolume_V1,
        sw1d_model.Set_TimeStep_V1,
    )
    ADD_METHODS = (
        sw1d_model.Pick_Inflow_V1,
        sw1d_model.Calc_WaterLevelDownstream_V1,
        sw1d_model.Calc_WaterLevel_V3,
        sw1d_model.Calc_WaterDepth_V2,
        sw1d_model.Calc_WettedArea_V1,
        sw1d_model.Calc_MaxTimeStep_V2,
        sw1d_model.Calc_DischargeVolume_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        channelinterfaces.StorageModel_V1,
    )
    SUBMODELS = ()

    storagemodeldownstream = modeltools.SubmodelProperty(
        channelinterfaces.StorageModel_V1, sidemodel=True
    )
    storagemodeldownstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodeldownstream_typeid = modeltools.SubmodelTypeIDProperty()

    routingmodelsdownstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        sidemodels=True,
    )


tester = Tester()
cythonizer = Cythonizer()
