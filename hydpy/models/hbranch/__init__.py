# -*- coding: utf-8 -*-
"""The HydPy-H-Branch model allows for branching the input from a
single inlet |Node| instance to an arbitrary number of outlet |Node|
instances.  In the original HBV96 implementation, it is supposed to
separate inflowing discharge, but in *HydPy* it can be used for
arbitrary variables.  Calculations are performed for each branch
individually by linear interpolation (or extrapolation) in accordance
with tabulated supporting points.
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

autodoc_basemodel()
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
