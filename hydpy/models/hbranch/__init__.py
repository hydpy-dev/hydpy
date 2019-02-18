# -*- coding: utf-8 -*-
"""The HydPy-H-Branch defines methods for branching single inflow values
into multiple outflow values.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
# ...from hbranch
from hydpy.models.hbranch.hbranch_control import ControlParameters
from hydpy.models.hbranch.hbranch_derived import DerivedParameters
from hydpy.models.hbranch.hbranch_fluxes import FluxSequences
from hydpy.models.hbranch.hbranch_inlets import InletSequences
from hydpy.models.hbranch.hbranch_outlets import OutletSequences
from hydpy.models.hbranch.hbranch_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
