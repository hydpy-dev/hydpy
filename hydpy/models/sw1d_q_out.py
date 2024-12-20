# pylint: disable=unused-wildcard-import
"""
The |sw1d.DOCNAME.long| model family member |sw1d_q_out| is a simple routing submodel,
which allows taking observed or previously simulated discharge series as "longitudinal"
channel outflow.

Please refer to the documentation of the "composite model" |sw1d_network|, where we
demonstrate and discuss |sw1d_q_out| in more detail (see the
:ref:`sw1d_network_bifurcations` example).
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import routinginterfaces

# ...from musk
from hydpy.models.sw1d import sw1d_model


class Model(sw1d_model.Main_CrossSectionModel_V2, routinginterfaces.RoutingModel_V3):
    """|sw1d_q_out.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="SW1D-Q-Out",
        description=(
            "submodel for subtracting pre-determined discharge from a channel outlet"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

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
        sw1d_model.Calc_WaterLevel_V3,
        sw1d_model.Calc_WaterDepth_WettedArea_CrossSectionModel_V2,
        sw1d_model.Calc_WaterDepth_WettedArea_V1,
        sw1d_model.Calc_MaxTimeStep_V4,
        sw1d_model.Calc_DischargeVolume_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        routinginterfaces.CrossSectionModel_V2,
        routinginterfaces.RoutingModel_V1,
        routinginterfaces.RoutingModel_V2,
        routinginterfaces.StorageModel_V1,
    )
    SUBMODELS = ()

    crosssection = modeltools.SubmodelProperty(routinginterfaces.CrossSectionModel_V2)

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
