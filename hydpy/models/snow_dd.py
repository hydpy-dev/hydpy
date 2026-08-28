# pylint: disable=line-too-long, unused-wildcard-import
"""ToDo"""

from hydpy.core import masktools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.interfaces import snowinterfaces
from hydpy.interfaces import stateinterfaces
from hydpy.interfaces import throughfallinterfaces
from hydpy.exe.modelimports import *
from hydpy.models.snow import snow_model
from hydpy.models.snow import snow_masks


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
        snow_model.Calc_AdjustedTemperature_V1,
        snow_model.Calc_RainSnowFraction_V1,
        snow_model.Calc_IceContent_WaterContent_V1,
        snow_model.Calc_IceLoss_WaterLoss_IceContent_WaterContent_V1,
        snow_model.Calc_IceGain_WaterGain_IceContent_WaterContent_V1,
        snow_model.Calc_MeltingFactor_V1,
        snow_model.Calc_PotentialMelt_V1,
        snow_model.Calc_PotentialFreeze_V1,
        snow_model.Calc_ActualMelt_IceContent_WaterContent_V1,
        snow_model.Calc_ActualFreeze_IceContent_WaterContent_V1,
        snow_model.Calc_Release_WaterContent_V1,
        snow_model.Calc_Snowpack_V1,  # ToDo: next
    )
    INTERFACE_METHODS = (
        snow_model.Process_SnowRoutine_V1,
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

        w = self.parameters.derived.zoneareafraction.values
        new = self.sequences.states
        old = initial_conditions["states"]
        ds = new.icecontent - old["icecontent"]
        dw = new.watercontent - old["watercontent"]
        return float(numpy.dot(w, numpy.mean(ds + dw, axis=0)))


class Masks(masktools.Masks):
    """Masks applicable to |snow_dd|."""

    CLASSES = snow_masks.Masks.CLASSES


tester = Tester()
cythonizer = Cythonizer()
