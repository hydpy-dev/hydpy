# pylint: disable=line-too-long, unused-wildcard-import

from hydpy.core import modeltools
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import snowinterfaces
from hydpy.exe.modelimports import *
from hydpy.models.snow import snow_model


class Model(snow_model.Main_PrecipModel,
    snow_model.Sub_SnowModel, snowinterfaces.SnowModel_V1):
    """|snow_dd.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Snow-DD", description="Degree-day-based snow modelling",
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
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty[
        precipinterfaces.PrecipModel_V1 | precipinterfaces.PrecipModel_V2](
        precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2
    )


tester = Tester()
cythonizer = Cythonizer()
