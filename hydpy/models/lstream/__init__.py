# -*- coding: utf-8 -*-

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
from hydpy.core.magictools import autodoc_basemodel
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

from hydpy.models.lstream.lstream_control import ControlParameters
from hydpy.models.lstream.lstream_derived import DerivedParameters
from hydpy.models.lstream.lstream_fluxes import FluxSequences
from hydpy.models.lstream.lstream_states import StateSequences
from hydpy.models.lstream.lstream_aides import AideSequences
from hydpy.models.lstream.lstream_inlets import InletSequences
from hydpy.models.lstream.lstream_outlets import OutletSequences
from hydpy.models.lstream.lstream_model import Model

autodoc_basemodel()
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
