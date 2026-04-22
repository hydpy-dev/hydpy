# pylint: disable=line-too-long, unused-wildcard-import
"""|evap_ret_makkink| is still under development.

Integration tests
=================

.. how_to_understand_integration_tests::

>>> from hydpy import Element
>>> from hydpy.models.evap_ret_makkink import *
>>> parameterstep()
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"

>>> nmbhru(1)
>>> hruarea(1.0)
>>> evapotranspirationfactor(1.0)

>>> with model.add_radiationmodel_v2("meteo_glob_io"):
...     pass
>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     temperatureaddend(0.0)

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> inputs.atmosphericpressure.series = 1001.0
>>> model.tempmodel.sequences.inputs.temperature.series = 15.9
>>> model.radiationmodel.sequences.inputs.globalradiation.series = 255.367464

.. integration-test::

    >>> test()
    |       date | atmosphericpressure | airtemperature | saturationvapourpressure | saturationvapourpressureslope | heatofcondensation | psychrometricconstant | globalradiation | netshortwaveradiation | referenceevapotranspiration | meanreferenceevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |              1001.0 |           15.9 |                18.067051 |                      1.154867 |          28.508773 |              0.665665 |      255.367464 |            196.632947 |                    2.843968 |                        2.843968 |
"""

from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import radiationinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2A,
    evap_model.Main_RadiationModel_V1,
    evap_model.Main_RadiationModel_V2,
    evap_model.Sub_ETModel,
    petinterfaces.PETModel_V1,
):
    """|evap_ret_makkink.DOCNAME.complete|.

    |evap_ret_makkink| can be used as a submodel:

    >>> from hydpy import pub, round_
    >>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
    >>> from hydpy.models.evap_pet_m import *
    >>> parameterstep()
    >>> nmbhru(3)
    >>> hruarea(0.5, 0.3, 0.2)
    >>> with model.add_retmodel_v1("evap_ret_makkink"):
    ...     evapotranspirationfactor(0.8, 1.0, 1.2)
    ...     inputs.atmosphericpressure = 1001.0
    ...     with model.add_radiationmodel_v2("meteo_glob_io"):
    ...         inputs.globalradiation = 255.367464
    ...     with model.add_tempmodel_v2("meteo_temp_io"):
    ...         temperatureaddend(0.0)
    ...         inputs.temperature = 15.9
    >>> model.calc_referenceevapotranspiration_v4()
    >>> fluxes.referenceevapotranspiration
    referenceevapotranspiration(2.275174, 2.843968, 3.412762)
    >>> round_(model.retmodel.get_meanpotentialevapotranspiration())
    2.67333
    """

    DOCNAME = modeltools.DocName(
        short="Evap-RET-Makkink", description="Makkink reference evapotranspiration"
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Process_RadiationModel_V1,
        evap_model.Calc_GlobalRadiation_V1,
        evap_model.Calc_NetShortwaveRadiation_V1,
        evap_model.Calc_AirTemperature_V1,
        evap_model.Calc_SaturationVapourPressure_V1,
        evap_model.Calc_SaturationVapourPressureSlope_V1,
        evap_model.Calc_PsychrometricConstant_V1,
        evap_model.Calc_HeatOfCondensation_V1,
        evap_model.Calc_ReferenceEvapotranspiration_V6,
        evap_model.Adjust_ReferenceEvapotranspiration_V1,
        evap_model.Calc_MeanReferenceEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V1,
        evap_model.Get_MeanPotentialEvapotranspiration_V1,
    )
    ADD_METHODS = (
        evap_model.Calc_AirTemperature_TempModel_V1,
        evap_model.Calc_AirTemperature_TempModel_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
        radiationinterfaces.RadiationModel_V1,
    )
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty[
        tempinterfaces.TempModel_V1 | tempinterfaces.TempModel_V2
    ](tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2)
    radiationmodel = modeltools.SubmodelProperty[
        radiationinterfaces.RadiationModel_V1 | radiationinterfaces.RadiationModel_V2
    ](radiationinterfaces.RadiationModel_V1, radiationinterfaces.RadiationModel_V2)


tester = Tester()
cythonizer = Cythonizer()
