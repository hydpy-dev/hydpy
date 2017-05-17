# -*- coding: utf-8 -*-
"""The HydPy-GlobWat model is defined in the package `globwat`.  In the following,
both terms are used synonymously.  Each of the following sections is related
to an individual module (e.g. `globwat_constants`, `globwat_model`...).

Constants
---------

.. automodule:: hydpy.models.globwat.globwat_constants
    :members:
    :show-inheritance:


Model
-----

.. automodule:: hydpy.models.globwat.globwat_model
    :members:
    :show-inheritance:

Parameters
----------
.. automodule:: hydpy.models.globwat.globwat_parameters
    :members:
    :show-inheritance:

Control parameters
..................
.. automodule:: hydpy.models.globwat.globwat_control
    :members:
    :show-inheritance:

Derived parameters
..................
.. automodule:: hydpy.models.globwat.globwat_derived
    :members:
    :show-inheritance:

Sequences
---------
.. automodule:: hydpy.models.globwat.globwat_sequences
    :members:
    :show-inheritance:

Input sequences
...............
.. automodule:: hydpy.models.globwat.globwat_inputs
    :members:
    :show-inheritance:

Flux sequences
..............
.. automodule:: hydpy.models.globwat.globwat_fluxes
    :members:
    :show-inheritance:

State sequences
...............
.. automodule:: hydpy.models.globwat.globwat_states
    :members:
    :show-inheritance:

Log sequences
.............
.. automodule:: hydpy.models.globwat.globwat_logs
    :members:
    :show-inheritance:

Aide sequences
..............
.. automodule:: hydpy.models.globwat.globwat_aides
    :members:
    :show-inheritance:

Link sequences
..............
.. automodule:: hydpy.models.globwat.globwat_links
    :members:
    :show-inheritance:
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...side packages
import numpy
from numpy import nan
# ...from Hydpy (framework)
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
# ...from HydPy (GlobWat)
from .globwat_constants import *
from .globwat_model import Model
from .globwat_parameters import Parameters
from .globwat_control import ControlParameters
from .globwat_derived import DerivedParameters
from .globwat_sequences import Sequences
from .globwat_inputs import InputSequences
from .globwat_fluxes import FluxSequences
from .globwat_states import StateSequences
#from .globwat_logs import LogSequences
#from .globwat_aides import AideSequences
from .globwat_links import InletSequences, OutletSequences

USECYTHON = False
"""Cython flag (False: pure Python mode, True: fast Python/Cython mode)."""

