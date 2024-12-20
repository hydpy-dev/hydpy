# pylint: disable=line-too-long, unused-wildcard-import
"""The primary purpose of |evap_ret_tw2002| is to serve as a submodel that provides
estimates of potential grass reference evapotranspiration following :cite:t:`ref-DVWK`,
as demonstrated for |lland_dd|.  However, you can also use it as a stand-alone model,
as it does not require interaction with a main model.  The following examples make use
of this stand-alone functionality.

|evap_ret_tw2002| requires two submodels.  One must follow the |RadiationModel_V1| or
the |RadiationModel_V2| interface and provide global radiation data; the other must
follow the |TempModel_V1| or the |TempModel_V2| interface and provide temperature data.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_ret_tw2002| requires no input from an external model and does
not supply any data to an outlet sequence.  Hence, assigning a model instance to a
blank |Element| instance is sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_ret_tw2002 import *
>>> parameterstep()
>>> element = Element("element")
>>> element.model = model

The implemented Turc-Wendling should be applied to daily data:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"

We set the parameter and input values in agreement with the
:ref:`evap_ret_fao56_hourly_simulation` example of |evap_ret_fao56|, which allows for
comparison with the results of the FAO reference evapotranspiration model applied to
data of station Uccle (Brussels, Belgium), as reported in example 18 of
:cite:t:`ref-Allen1998`:

>>> nmbhru(1)
>>> hruarea(1.0)
>>> evapotranspirationfactor(1.0)
>>> hrualtitude(100.0)

|evap_ret_fao56| has no counterpart for the |CoastFactor| parameter.  We set its value from
our gut feeling to 0.9, as Brussels is not directly adjacent to the coastline (0.6) but
also not that far away from it (1.0):

>>> coastfactor(0.9)

A |meteo_glob_io| and a |meteo_temp_io| submodel provide the required global radiation
and temperature data:

>>> with model.add_radiationmodel_v2("meteo_glob_io"):
...     pass
>>> with model.add_tempmodel_v2("meteo_temp_io"):
...     temperatureaddend(1.0)

Now, we can initialise an |IntegrationTest| object and set the required meteorological
input:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> model.tempmodel.sequences.inputs.temperature.series = 15.9
>>> model.radiationmodel.sequences.inputs.globalradiation.series = 255.367464

For the example at hand, there is an excellent agreement with the result calculated by
|evap_ret_fao56| and given by :cite:t:`ref-Allen1998`, which is 3.75 mm/d:

.. integration-test::

    >>> test()
    |       date | airtemperature | globalradiation | referenceevapotranspiration | meanreferenceevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           16.9 |      255.367464 |                    3.787245 |                        3.787245 |

Instead of IO submodels, one could use the main model of |evap_ret_tw2002| for
providing the temperature data or a "real" submodel that calculates the global
radiation data.  The first option is not feasible here due to not using
|evap_ret_tw2002| as a submodel but as a stand-alone model.  But we can demonstrate the
latter option by using, for example, |meteo_glob_fao56|, which we also configure in
agreement with the :ref:`evap_ret_fao56_hourly_simulation` example.  Hence,
|meteo_glob_fao56| reproduces the global radiation above so that |evap_ret_tw2002|
calculates the same potential evapotranspiration value:

>>> with model.add_radiationmodel_v1("meteo_glob_fao56"):
...     latitude(50.8)
...     angstromconstant(0.25)
...     angstromfactor(0.5)

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"
>>> model.tempmodel.sequences.inputs.temperature.series = 15.9
>>> model.radiationmodel.sequences.inputs.sunshineduration.series = 9.25

.. integration-test::

    >>> test()
    |       date | airtemperature | globalradiation | referenceevapotranspiration | meanreferenceevapotranspiration |
    -----------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           16.9 |      255.367464 |                    3.787245 |                        3.787245 |

"""
# import...
# ...from HydPy
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
    """|evap_ret_tw2002.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Evap-RET-TW2002",
        description="Turc-Wendling reference evapotranspiration, 2002",
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Process_RadiationModel_V1,
        evap_model.Calc_GlobalRadiation_V1,
        evap_model.Calc_AirTemperature_V1,
        evap_model.Calc_ReferenceEvapotranspiration_V2,
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

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    radiationmodel = modeltools.SubmodelProperty(
        radiationinterfaces.RadiationModel_V1, radiationinterfaces.RadiationModel_V2
    )


tester = Tester()
cythonizer = Cythonizer()
