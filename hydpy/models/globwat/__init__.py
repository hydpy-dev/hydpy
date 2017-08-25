# -*- coding: utf-8 -*-
"""The HydPy-GlobWat model is defined in the package `globwat`. Each of the
following sections is related to an individual module (e.g. `globwat_constants`
, `globwat_model`...).
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy.core.modelimports import *
# ...from globwat
from hydpy.models.globwat.globwat_constants import *
from hydpy.models.globwat.globwat_model import Model
from hydpy.models.globwat.globwat_parameters import Parameters
from hydpy.models.globwat.globwat_control import ControlParameters
from hydpy.models.globwat.globwat_derived import DerivedParameters
from hydpy.models.globwat.globwat_sequences import Sequences
from hydpy.models.globwat.globwat_inputs import InputSequences
from hydpy.models.globwat.globwat_fluxes import FluxSequences
from hydpy.models.globwat.globwat_states import StateSequences
from hydpy.models.globwat.globwat_inlets import InletSequences
from hydpy.models.globwat.globwat_outlets import OutletSequences

autodoc_basemodel()
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
