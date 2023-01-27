# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the Turc-Wendling reference evapotranspiration model
:cite:p:`ref-DVWK`.

The primary purpose of |evap_tw2002| is to serve as a submodel that provides estimates
of potential grass reference evapotranspiration (as demonstrated for |lland_v1|).
However, you can also use it as a stand-alone model, as it does not require interaction
with a main model.  The following examples make use of this stand-alone functionality.

Integration tests
=================

.. how_to_understand_integration_tests::

Application model |evap_tw2002| requires no input from another model and does not supply
any outlet sequence.  Hence, assigning a model instance to a blank |Element| instance
is sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_tw2002 import *
>>> parameterstep()
>>> element = Element("element")
>>> element.model = model

The implemented Turc-Wendling should be applied to daily data:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-07-06", "2000-07-07", "1d"
>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

We set the parameter and input values in agreement with the
:ref:`evap_fao56_hourly_simulation` example of |evap_fao56|, which allows for
comparison with the results of the FAO reference evapotranspiration model applied to
data of station Uccle (Brussels, Belgium), as reported in example 18 of
:cite:t:`ref-Allen1998`:

>>> nmbhru(1)
>>> hruarea(1.0)
>>> airtemperatureaddend(1.0)
>>> evapotranspirationfactor(1.0)
>>> altitude(100.0)
>>> inputs.airtemperature.series = 15.9
>>> inputs.globalradiation.series = 255.367464

|evap_fao56| has no counterpart for the |CoastFactor| parameter.  We set its value from
our gut feeling to 0.9, as Brussels is not directly adjacent to the coastline (0.6) but
also not that far away from it (1.0):

>>> coastfactor(0.9)

For the example at hand, there is an excellent agreement with the result calculated by
|evap_fao56| and given by :cite:t:`ref-Allen1998`, which is 3.75 mm/d:

.. integration-test::

    >>> test()
    |       date | airtemperature | globalradiation | adjustedairtemperature | referenceevapotranspiration | meanreferenceevapotranspiration |
    ------------------------------------------------------------------------------------------------------------------------------------------
    | 2000-06-07 |           15.9 |      255.367464 |                   16.9 |                    3.787245 |                        3.787245 |
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.interfaces import petinterfaces
from hydpy.models.evap import evap_model


class Model(modeltools.AdHocModel, petinterfaces.PETModel_V1):
    """The Turc-Wendling version of HydPy-Evap."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_AdjustedAirTemperature_V1,
        evap_model.Calc_ReferenceEvapotranspiration_V2,
        evap_model.Adjust_ReferenceEvapotranspiration_V1,
        evap_model.Calc_MeanReferenceEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V1,
        evap_model.Get_MeanPotentialEvapotranspiration_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
