# -*- coding: utf-8 -*-
"""
The base model |test| is intended for implementing small application model
that allow for testing or demonstrating specific features of the HydPy
framework.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
# ...from test
from hydpy.models.test.test_control import ControlParameters
from hydpy.models.test.test_solver import SolverParameters
from hydpy.models.test.test_fluxes import FluxSequences
from hydpy.models.test.test_states import StateSequences
from hydpy.models.test.test_model import Model

autodoc_basemodel()
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()