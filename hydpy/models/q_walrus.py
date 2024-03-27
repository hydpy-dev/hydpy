# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""Implementation of the equation suggested by :cite:t:`ref-Brauer2014` for calculating
the outflow of subcatchment through a ditch or channel.

|q_walrus| is a submodel that supplies its main model with discharge estimates.  It
assumes a rectangular channel geometry and, optionally, the existence of a weir at the
channel outlet.  See `issue 120`_ for more additional information.

.. _`issue 120`: https://github.com/hydpy-dev/hydpy/issues/120

As |q_walrus| only applies the single method |Calculate_Discharge_V1|, we keep the
tests short and take a single example from its documentation:

>>> from hydpy.models.q_walrus import *
>>> simulationstep("12h")
>>> parameterstep("1d")
>>> channeldepth(5.0)
>>> crestheight(2.0)
>>> bankfulldischarge(2.0)
>>> dischargeexponent(2.0)
>>> crestheighttolerance(0.1)
>>> derived.crestheightregularisation.update()
>>> from hydpy import round_
>>> round_(model.calculate_discharge(3.0))
0.111111
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *

# ...from ga
from hydpy.models.q import q_model


class Model(modeltools.AdHocModel, q_model.Base_DischargeModel_V2):
    """The WALRUS version of HydPy-Q for calculating the flow out of a ditch or
    channel."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (q_model.Calculate_Discharge_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
