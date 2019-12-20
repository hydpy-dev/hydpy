# -*- coding: utf-8 -*-
"""
The L-Stream model defines the methods and classes required for
performing  flood routing calculations after the Williams method
as implemented in LARSIM.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.auxs.anntools import ann
# ...from lstream
from hydpy.models.lstream.lstream_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
