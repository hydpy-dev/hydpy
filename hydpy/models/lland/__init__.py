# -*- coding: utf-8 -*-
"""
Constants
---------

.. automodule:: hydpy.models.lland.lland_constants
    :members:
    :show-inheritance:

Model
-----

.. automodule:: hydpy.models.lland.lland_model
    :members:
    :show-inheritance:

Parameters
----------

.. automodule:: hydpy.models.lland.lland_parameters
    :members:
    :show-inheritance:

Control parameters
..................

.. automodule:: hydpy.models.lland.lland_control
    :members:
    :show-inheritance:


Derived parameters
..................

.. automodule:: hydpy.models.lland.lland_derived
    :members:
    :show-inheritance:

Sequences
---------

.. automodule:: hydpy.models.lland.lland_sequences
    :members:
    :show-inheritance:

Input sequences
...............

.. automodule:: hydpy.models.lland.lland_inputs
    :members:
    :show-inheritance:

Flux sequences
..............

.. automodule:: hydpy.models.lland.lland_fluxes
    :members:
    :show-inheritance:

State sequences
...............

.. automodule:: hydpy.models.lland.lland_states
    :members:
    :show-inheritance:

Log sequences
.............

.. automodule:: hydpy.models.lland.lland_logs
    :members:
    :show-inheritance:

Aide sequences
..............

.. automodule:: hydpy.models.lland.lland_aides
    :members:
    :show-inheritance:

Link sequences
..............

.. automodule:: hydpy.models.lland.lland_links
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
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

from hydpy.models.lland.lland_constants import (SIED_D, SIED_L, VERS, ACKER,
                                                WEINB, OBSTB, BODEN, GLETS,
                                                GRUE_I, FEUCHT, GRUE_E, BAUMB,
                                                NADELW, LAUBW, MISCHW, WASSER)
from hydpy.models.lland.lland_parameters import Parameters
from hydpy.models.lland.lland_control import ControlParameters
from hydpy.models.lland.lland_derived import DerivedParameters
from hydpy.models.lland.lland_sequences import Sequences
from hydpy.models.lland.lland_inputs import InputSequences
from hydpy.models.lland.lland_fluxes import FluxSequences
from hydpy.models.lland.lland_states import StateSequences
from hydpy.models.lland.lland_aides import AideSequences
from hydpy.models.lland.lland_links import OutletSequences
from hydpy.models.lland.lland_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()


