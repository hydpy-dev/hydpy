# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""
The |sw1d.DOCNAME.long| model family member |sw1d_lias| is a routing submodel that
allows applying a 1-dimensional version of the "local inertial approximation of the
shallow water equations" introduced by :cite:t:`ref-Bates2010` and "stabilised" by
:cite:t:`ref-Almeida2012`.

Please refer to the documentation of the "user model" |sw1d_channel| and the
"composite model" |sw1d_network|, where we demonstrate and discuss |sw1d_lias| in
detail.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import routinginterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(sw1d_model.Main_CrossSectionModel_V2, routinginterfaces.RoutingModel_V2):
    """|sw1d_lias.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="SW1D-LIAS",
        description=(
            "submodel for calculating the discharge between two channel segments "
            "based on Bates et al. (2010) and Almeida et al. (2012)"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

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
        sw1d_model.Calc_WaterLevel_V1,
        sw1d_model.Calc_WaterDepth_WettedArea_WettedPerimeter_CrossSectionModel_V2,
        sw1d_model.Calc_WaterDepth_WettedArea_WettedPerimeter_V1,
        sw1d_model.Calc_MaxTimeStep_V1,
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
        routinginterfaces.CrossSectionModel_V2,
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.RoutingModel_V3,
        routinginterfaces.StorageModel_V1,
    )
    SUBMODELS = ()

    crosssection = modeltools.SubmodelProperty(routinginterfaces.CrossSectionModel_V2)

    storagemodelupstream = modeltools.SubmodelProperty(
        routinginterfaces.StorageModel_V1, sidemodel=True
    )
    storagemodelupstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodelupstream_typeid = modeltools.SubmodelTypeIDProperty()

    storagemodeldownstream = modeltools.SubmodelProperty(
        routinginterfaces.StorageModel_V1, sidemodel=True
    )
    storagemodeldownstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodeldownstream_typeid = modeltools.SubmodelTypeIDProperty()

    routingmodelsupstream = modeltools.SubmodelsProperty(
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        sidemodels=True,
    )

    routingmodelsdownstream = modeltools.SubmodelsProperty(
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.RoutingModel_V3,
        sidemodels=True,
    )


tester = Tester()
cythonizer = Cythonizer()
