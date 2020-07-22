# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""
Version 1 of the dummy model serves as a temporary placeholder model.
In each simulation step, it simply sums up its inputs and hands the
resulting value to the downstream node without modifications.

Integration test:

    We prepare a simulation period of three days:

    >>> from hydpy import pub
    >>> pub.timegrids = '2000-01-01', '2000-01-04', '1d'

    The model object does not require any parameter information:

    >>> from hydpy.models.dummy_v1 import *
    >>> parameterstep()

    We add the model object to an element connected to two inlet nodes
    and one outlet node and prepare a runnable test object:

    >>> from hydpy import Element, IntegrationTest
    >>> element = Element('element',
    ...                   inlets=('inlet1', 'inlet2'),
    ...                   outlets='outlet')
    >>> element.model = model
    >>> test = IntegrationTest(element)

    After defining two input series, we can demonstrate that each pair
    of values of the inlet nodes is summed up and handed to the outlet node:

    >>> element.inlets.inlet1.sequences.sim.series = 0.0, 1.0, 2.0
    >>> element.inlets.inlet2.sequences.sim.series = 0.0, 2.0, -4.0
    >>> test()
    |                date |    q | inlet1 | inlet2 | outlet |
    ---------------------------------------------------------
    | 2000-01-01 00:00:00 |  0.0 |    0.0 |    0.0 |    0.0 |
    | 2000-01-02 00:00:00 |  3.0 |    1.0 |    2.0 |    3.0 |
    | 2000-01-03 00:00:00 | -2.0 |    2.0 |   -4.0 |   -2.0 |
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
# ...from dummy
from hydpy.models.dummy import dummy_model


class Model(modeltools.AdHocModel):
    """The HydPy-Dummy model."""
    INLET_METHODS = (
        dummy_model.Pick_Q_V1,
    )
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    ADD_METHODS = ()
    OUTLET_METHODS = (
        dummy_model.Pass_Q_V1,
    )
    SENDER_METHODS = ()
    SUBMODELS = ()
