# -*- coding: utf-8 -*-
"""
The L-Lake model defines the methods and classes required for
performing lake and dam retention processes as implemented in
LARSIM.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from llake
from hydpy.models.llake.llake_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
