# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""
|dummy_snowycanopy| merely serves testing purposes.  We use it, for example, to perform
the integration tests for submodels like |evap_aet_morsim| without the need to couple
them to complex main models like |lland_knauf| for providing snow interception data.

Integration test
================

The only functionality of |dummy_snowycanopy| is reading input time series.  Hence,
configuring and testing it does not require additional explanations:

>>> from hydpy.models.dummy_snowycanopy import *
>>> parameterstep()
>>> from hydpy import Element
>>> element = Element("element")
>>> element.model = model

>>> from hydpy import IntegrationTest, pub, round_
>>> pub.timegrids = "2000-01-01", "2000-01-03", "1d"
>>> nmbzones(2)

>>> test = IntegrationTest(element)
>>> test.dateformat = "%Y-%d-%m"

>>> inputs.snowycanopy.series = [[1.0, 2.0], [3.0, 4.0]]

.. integration-test::

    >>> test()
    |       date |      snowycanopy |
    ---------------------------------
    | 2000-01-01 | 1.0          2.0 |
    | 2000-02-01 | 3.0          4.0 |

>>> round_(model.get_snowycanopy_v1(1))
4.0
"""
# import...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.models.dummy import dummy_control
from hydpy.models.dummy import dummy_model
from hydpy.interfaces import stateinterfaces

ADDITIONAL_CONTROLPARAMETERS = (dummy_control.NmbZones,)


class Model(modeltools.AdHocModel, stateinterfaces.SnowyCanopyModel_V1):
    """|dummy_snowycanopy.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Dummy-SnowyCanopy",
        description=(
            "dummy model supplying main models with snow cover degrees in canopies"
        ),
    )
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (dummy_model.Get_SnowyCanopy_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    @importtools.define_targetparameter(dummy_control.NmbZones)
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of zones.

        >>> from hydpy.models.dummy_snowcover import *
        >>> parameterstep()
        >>> model.prepare_nmbzones(2)
        >>> nmbzones
        nmbzones(2)
        """
        self.parameters.control.nmbzones(nmbzones)


tester = Tester()
cythonizer = Cythonizer()
