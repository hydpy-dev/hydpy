# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""
The *HydPy-SW1D* model family member |sw1d_lias| is a routing submodel that allows
applying a 1-dimensional version of the "local inertial approximation of the shallow
water equations" introduced by :cite:t:`ref-Bates2010` and "stabilised" by
:cite:t:`ref-Almeida2012`.

Please refer to the documentation of the "user model" |sw1d_channel| and the
"composite model" |sw1d_network|, where we demonstrate and discuss |sw1d_lias| in
detail.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import channelinterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(modeltools.AdHocModel, channelinterfaces.RoutingModel_V2):
    """A routing submodel based on the "local inertial approximation of the shallow
    water equations" introduced by :cite:t:`ref-Bates2010` and "stabilised" by
    :cite:t:`ref-Almeida2012`."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        sw1d_model.Perform_Preprocessing_V2,
        sw1d_model.Determine_MaxTimeStep_V1,
        sw1d_model.Determine_Discharge_V1,
        sw1d_model.Perform_Postprocessing_V2,
        sw1d_model.Get_MaxTimeStep_V1,
        sw1d_model.Get_Discharge_V1,
        sw1d_model.Get_PartialDischargeUpstream_V1,
        sw1d_model.Get_PartialDischargeDownstream_V1,
        sw1d_model.Get_DischargeVolume_V1,
        sw1d_model.Set_TimeStep_V1,
    )
    ADD_METHODS = (
        sw1d_model.Reset_DischargeVolume_V1,
        sw1d_model.Calc_WaterVolumeUpstream_V1,
        sw1d_model.Calc_WaterVolumeDownstream_V1,
        sw1d_model.Calc_WaterLevelUpstream_V1,
        sw1d_model.Calc_WaterLevelDownstream_V1,
        sw1d_model.Calc_WaterLevel_V2,
        sw1d_model.Calc_WaterDepth_V2,
        sw1d_model.Calc_MaxTimeStep_V1,
        sw1d_model.Calc_WettedArea_V1,
        sw1d_model.Calc_WettedPerimeter_V1,
        sw1d_model.Calc_DischargeUpstream_V1,
        sw1d_model.Calc_DischargeDownstream_V1,
        sw1d_model.Calc_Discharge_V1,
        sw1d_model.Update_Discharge_V1,
        sw1d_model.Update_DischargeVolume_V1,
        sw1d_model.Pass_Discharge_V1,
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

    storagemodelupstream = modeltools.SubmodelProperty(
        channelinterfaces.StorageModel_V1, sidemodel=True
    )
    storagemodelupstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodelupstream_typeid = modeltools.SubmodelTypeIDProperty()

    storagemodeldownstream = modeltools.SubmodelProperty(
        channelinterfaces.StorageModel_V1, sidemodel=True
    )
    storagemodeldownstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodeldownstream_typeid = modeltools.SubmodelTypeIDProperty()

    routingmodelsupstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        sidemodels=True,
    )

    routingmodelsdownstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        sidemodels=True,
    )


tester = Tester()
cythonizer = Cythonizer()
