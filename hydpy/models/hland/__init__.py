# -*- coding: utf-8 -*-
"""
Constants
---------

.. automodule:: hydpy.models.hland.hland_constants
    :members:
    :show-inheritance:

Model
-----

.. automodule:: hydpy.models.hland.hland_model
    :members:
    :show-inheritance:

Parameters
----------

.. automodule:: hydpy.models.hland.hland_parameters
    :members:
    :show-inheritance:

Control parameters
..................

.. automodule:: hydpy.models.hland.hland_control
    :members:
    :show-inheritance:


Derived parameters
..................

.. automodule:: hydpy.models.hland.hland_derived
    :members:
    :show-inheritance:

Sequences
---------

.. automodule:: hydpy.models.hland.hland_sequences
    :members:
    :show-inheritance:

Input sequences
...............

.. automodule:: hydpy.models.hland.hland_inputs
    :members:
    :show-inheritance:

Flux sequences
..............

.. automodule:: hydpy.models.hland.hland_fluxes
    :members:
    :show-inheritance:

State sequences
...............

.. automodule:: hydpy.models.hland.hland_states
    :members:
    :show-inheritance:

Log sequences
.............

.. automodule:: hydpy.models.hland.hland_logs
    :members:
    :show-inheritance:

Aide sequences
..............

.. automodule:: hydpy.models.hland.hland_aides
    :members:
    :show-inheritance:

Link sequences
..............

.. automodule:: hydpy.models.hland.hland_links
    :members:
    :show-inheritance:

"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...third party
import numpy
from numpy import nan
# ...HydPy specific
# Load the required `magic` functions into the local namespace.
from hydpy.framework.magictools import parameterstep
from hydpy.framework.magictools import simulationstep
from hydpy.framework.magictools import controlcheck
from hydpy.framework.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

from hland_constants import FIELD, FOREST, GLACIER, ILAKE
from hland_parameters import Parameters
from hland_control import ControlParameters
from hland_derived import DerivedParameters
from hland_sequences import Sequences
from hland_inputs import InputSequences
from hland_fluxes import FluxSequences
from hland_states import StateSequences
from hland_aides import AideSequences
from hland_logs import LogSequences
from hland_links import OutletSequences
from hland_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()


