# -*- coding: utf-8 -*-
"""The HydPy-H-Branch defines methods for branching single inflow values
into multiple outflow values.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
# ...from hbranch
from hydpy.models.hbranch.hbranch_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
