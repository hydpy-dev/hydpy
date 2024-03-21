# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the potential evapotranspiration routines of HBV96
:cite:p:`ref-Lindstrom1997HBV96`.

The primary purpose of |evap_pet_hbv96| is to serve as a submodel that provides
estimates of potential evapotranspiration.  Of course, you can connect it to |hland_v1|
if you long for a close HBV96 emulation, but it also works with other main models like
|lland_v1| or |wland_v001|.

|evap_pet_hbv96| itself requires other models for determining temperature and
precipitation.  By default, it queries the already available data from its main model.
Alternatively, it can handle its own submodels.  The following tests rely on the latter
option.

Integration test
================

.. how_to_understand_integration_tests::

According to the intended usage as a submodel, |evap_pet_hbv96| requires no connections
to any nodes.  Hence, assigning a model instance to a blank |Element| instance is
sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_pet_hbv96 import *
>>> parameterstep("1h")
>>> element = Element("element")
>>> element.model = model

We perform the integration test for a single simulation step, the first hour of the
second day of the simulation period selected for the integration tests of |hland_v1|:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-02 00:00", "2000-01-02 01:00", "1h"

We set all parameter values identical to the ones defined in the :ref:`hland_v1_field`
example of |hland_v1|:

>>> nmbhru(1)
>>> hruarea(1.0)
>>> hrualtitude(100.0)
>>> evapotranspirationfactor(0.7)
>>> airtemperaturefactor(0.1)
>>> altitudefactor(-0.1)
>>> precipitationfactor(0.1)

A |meteo_temp_io| submodel provides the required temperature, and a |meteo_precip_io|
submodel the required precipitation:

>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     temperatureaddend(0.0)
>>> with model.add_precipmodel_v2("meteo_precip_io"):
...     precipitationfactor(1.0)

Now we can initialise an |IntegrationTest| object:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m %H:00"

The following meteorological input also stems from the input data of the
:ref:`hland_v1_field` example:

>>> inputs.normalairtemperature.series = 18.2
>>> inputs.normalevapotranspiration.series = 0.097474
>>> model.tempmodel.sequences.inputs.temperature.series = 19.2

The following precipitation value is from the results table of the
:ref:`hland_v1_field` example:

>>> model.precipmodel.sequences.inputs.precipitation.series = 0.847

The following simulation results contain the calculated reference and potential
evapotranspiration.  Reference evapotranspiration is not available in the results of
the :ref:`hland_v1_field` example of |hland_v1|.  The potential evapotranspiration
estimate is the same in both tables:

.. integration-test::

    >>> test()
    |        date | normalairtemperature | normalevapotranspiration | meanairtemperature | precipitation | referenceevapotranspiration | potentialevapotranspiration | meanpotentialevapotranspiration |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 02/01 00:00 |                 18.2 |                 0.097474 |               19.2 |         0.847 |                    0.075055 |                     0.06896 |                         0.06896 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_TempModel_V1,
    evap_model.Main_TempModel_V2A,
    evap_model.Main_PrecipModel_V1,
    evap_model.Main_PrecipModel_V2A,
    evap_model.Sub_ETModel,
    petinterfaces.PETModel_V1,
):
    """The HBV96 version of HydPy-Evap for calculating potential evapotranspiration."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_MeanAirTemperature_V1,
        evap_model.Calc_Precipitation_V1,
        evap_model.Calc_ReferenceEvapotranspiration_V5,
        evap_model.Adjust_ReferenceEvapotranspiration_V1,
        evap_model.Calc_PotentialEvapotranspiration_V3,
        evap_model.Calc_MeanPotentialEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V2,
        evap_model.Get_MeanPotentialEvapotranspiration_V2,
    )
    ADD_METHODS = (
        evap_model.Calc_MeanAirTemperature_TempModel_V1,
        evap_model.Calc_MeanAirTemperature_TempModel_V2,
        evap_model.Calc_Precipitation_PrecipModel_V1,
        evap_model.Calc_Precipitation_PrecipModel_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
        precipinterfaces.PrecipModel_V1,
        precipinterfaces.PrecipModel_V2,
    )
    SUBMODELS = ()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2
    )


tester = Tester()
cythonizer = Cythonizer()
