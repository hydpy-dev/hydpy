# pylint: disable=line-too-long, unused-wildcard-import
"""ToDo"""
from hydpy.core import modeltools
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import snowinterfaces
from hydpy.exe.modelimports import *
from hydpy.models.snow import snow_model


class Model(
    snow_model.Main_PrecipModel, snow_model.Sub_SnowModel, snowinterfaces.SnowModel_V1
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
        snow_model.Calc_Precipitation_PrecipModel_V1,
        snow_model.Calc_Precipitation_PrecipModel_V2,
    )
    RUN_METHODS = (
        snow_model.Calc_Precipitation_V1,
        snow_model.Calc_PotentialSnowmelt_V1,
        snow_model.Calc_Snowmelt_Snowpack_V1,
    )
    INTERFACE_METHODS = (snow_model.Determine_Release_V1, snow_model.Get_Release_V1)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty[
        precipinterfaces.PrecipModel_V1 | precipinterfaces.PrecipModel_V2
    ](precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2)

    def get_waterbalance(self, initial_conditions: ConditionsSubmodel) -> float:
        """Return the water balance after the submodel has been executed."""

        areas = self.parameters.control.hruarea.values
        diff = self.sequences.states.snowpack - initial_conditions["states"]["snowpack"]
        return float(numpy.dot(areas, diff) / numpy.sum(areas))



tester = Tester()
cythonizer = Cythonizer()
