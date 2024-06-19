# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""
The |sw1d.DOCNAME.long| model family member |sw1d_weir_out| is a routing submodel,
which calculates the free flow over a weir out of a channel after Poleni.

Please refer to the documentation of the "user model" |sw1d_channel| and the
"composite model" |sw1d_network|, where we demonstrate and discuss |sw1d_weir_out| in
more detail (see, for example, `:ref:`sw1d_channel_weir_outflow`).
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import routinginterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(modeltools.AdHocModel, routinginterfaces.RoutingModel_V3):
    """|sw1d_weir_out.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="SW1D-Weir-Out",
        description="submodel for calculating free weir flow at a channel outlet",
    )

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        sw1d_model.Perform_Preprocessing_V2,
        sw1d_model.Determine_MaxTimeStep_V3,
        sw1d_model.Determine_Discharge_V3,
        sw1d_model.Get_MaxTimeStep_V1,
        sw1d_model.Get_Discharge_V1,
        sw1d_model.Get_PartialDischargeDownstream_V1,
        sw1d_model.Get_DischargeVolume_V1,
        sw1d_model.Set_TimeStep_V1,
        sw1d_model.Perform_Postprocessing_V2,
    )
    ADD_METHODS = (
        sw1d_model.Reset_DischargeVolume_V1,
        sw1d_model.Calc_WaterLevelUpstream_V1,
        sw1d_model.Calc_WaterLevel_V3,
        sw1d_model.Calc_MaxTimeStep_V3,
        sw1d_model.Calc_Discharge_V2,
        sw1d_model.Update_DischargeVolume_V1,
        sw1d_model.Pass_Discharge_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.StorageModel_V1,
    )
    SUBMODELS = ()

    storagemodelupstream = modeltools.SubmodelProperty(
        routinginterfaces.StorageModel_V1, sidemodel=True
    )
    storagemodelupstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodelupstream_typeid = modeltools.SubmodelTypeIDProperty()

    routingmodelsupstream = modeltools.SubmodelsProperty(
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        sidemodels=True,
    )


tester = Tester()
cythonizer = Cythonizer()
