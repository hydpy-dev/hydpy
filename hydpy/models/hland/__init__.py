# -*- coding: utf-8 -*-
"""
The H-Land model is the core of the HydPy implementation of the
the frequently applied HBV96 model.  It consists of some routines
for the preparation of meteorological input, and some process
routines related to interception, snow, soil moisture, upper
groundwater, lower groundwater (including lakes), and runoff
concentration.
"""
# import..
# ...from HydPy
from hydpy.exe.modelimports import *
# ...from hland
from hydpy.models.hland.hland_constants import FIELD, FOREST, GLACIER, ILAKE
from hydpy.models.hland.hland_control import ControlParameters
from hydpy.models.hland.hland_derived import DerivedParameters
from hydpy.models.hland.hland_inputs import InputSequences
from hydpy.models.hland.hland_fluxes import FluxSequences
from hydpy.models.hland.hland_states import StateSequences
from hydpy.models.hland.hland_logs import LogSequences
from hydpy.models.hland.hland_outlets import OutletSequences
from hydpy.models.hland.hland_masks import Masks
from hydpy.models.hland.hland_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
