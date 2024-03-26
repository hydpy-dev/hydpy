# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""
The *HydPy-SW1D* model family member |sw1d_q_out| is a simple routing submodel, which
allows taking observed or previously simulated discharge series as "longitudinal"
channel outflow.

Please refer to the documentation of the "composite model" |sw1d_network|, where we
demonstrate and discuss |sw1d_q_out| in more detail (see the
:ref:`sw1d_network_bifurcations` example).
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import channelinterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(modeltools.AdHocModel, channelinterfaces.RoutingModel_V3):
    """A simple routing submodel for removing "longitudinal" outflow from the last
    segment of a channel."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        sw1d_model.Perform_Preprocessing_V4,
        sw1d_model.Determine_MaxTimeStep_V4,
        sw1d_model.Determine_Discharge_V4,
        sw1d_model.Perform_Postprocessing_V4,
        sw1d_model.Get_MaxTimeStep_V1,
        sw1d_model.Get_Discharge_V1,
        sw1d_model.Get_PartialDischargeDownstream_V1,
        sw1d_model.Get_DischargeVolume_V1,
        sw1d_model.Set_TimeStep_V1,
    )
    ADD_METHODS = (
        sw1d_model.Pick_Outflow_V1,
        sw1d_model.Calc_WaterLevelUpstream_V1,
        sw1d_model.Calc_WaterLevel_V4,
        sw1d_model.Calc_WaterDepth_V2,
        sw1d_model.Calc_WettedArea_V1,
        sw1d_model.Calc_MaxTimeStep_V4,
        sw1d_model.Calc_DischargeVolume_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.StorageModel_V1,
    )
    SUBMODELS = ()

    storagemodelupstream = modeltools.SubmodelProperty(
        channelinterfaces.StorageModel_V1, sidemodel=True
    )
    storagemodelupstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodelupstream_typeid = modeltools.SubmodelTypeIDProperty()

    routingmodelsupstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        sidemodels=True,
    )


tester = Tester()
cythonizer = Cythonizer()
