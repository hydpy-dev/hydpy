# -*- coding: utf-8 -*-
"""
The L-Stream model defines the methods and classes required for
performing  flood routing calculations after the Williams method
as implemented in LARSIM.
"""
# import...
# ...from HydPy
from hydpy.core.modelimports import *
# ...from lstream
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
