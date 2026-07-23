# pylint: disable=line-too-long, unused-wildcard-import
"""ToDo"""

from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import snowinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.interfaces import throughfallinterfaces
from hydpy.exe.modelimports import *
from hydpy.models.snow import snow_control
from hydpy.models.snow import snow_model

ADDITIONAL_CONTROLPARAMETERS = (snow_control.ZoneArea, snow_control.ZoneHeight)  # ToDo


class Model(
    snow_model.Main_ThroughfallModel,
    snow_model.Sub_SnowModel,
    snowinterfaces.SnowModel_V1,
    stateinterfaces.SnowCoverModel_V1,
):
    """|snow_dd.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Snow-DD", description="Degree-day-based snow modelling"
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        snow_model.Calc_Throughfall_ThroughfallModel_V1,
        snow_model.Calc_Throughfall_ThroughfallModel_V2,
    )
    RUN_METHODS = (
        snow_model.Calc_Throughfall_V1,
        snow_model.Calc_Snowpack_WaterContent_V1,
        # snow_model.Calc_SPL_WCL_SP_WC_V1,
        # snow_model.Calc_SPG_WCG_SP_WC_V1,
        snow_model.Calc_MeltingFactor_V1,
        snow_model.Calc_PotentialMelt_V1,
        snow_model.Calc_Melt_SP_WC_V1,
        snow_model.Calc_Refr_SP_WC_V1,
        snow_model.Calc_In_WC_V1,
        snow_model.Calc_SWE_V1,
    )
    INTERFACE_METHODS = (
        snow_model.Determine_Release_V1,
        snow_model.Get_Release_V1,
        snow_model.Get_SnowCover_V1,
        snow_model.Computes_SnowEvaporation_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    throughfallmodel = modeltools.SubmodelProperty[
        throughfallinterfaces.ThroughfallModel_V1
        | throughfallinterfaces.ThroughfallModel_V2
    ](
        throughfallinterfaces.ThroughfallModel_V1,
        throughfallinterfaces.ThroughfallModel_V2,
    )

    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Return the water balance after the submodel has been executed."""

        areas = self.parameters.control.hruarea.values
        diff = self.sequences.states.snowpack - initial_conditions["states"]["snowpack"]
        return float(numpy.dot(areas, diff) / numpy.sum(areas))


tester = Tester()
cythonizer = Cythonizer()
