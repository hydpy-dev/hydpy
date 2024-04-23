# -*- coding: utf-8 -*-
"""
The G-Land model is the core of the HydPy implementation of the frequently applied
Génie Rurale models. Currently the versions, GR4, GR5 and GR6 are implemented.
For the modelling of snow processes within the G-Land processes the seperate CEMA-Neige
snow module is implemented.
"""
# import..
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from gland
from hydpy.models.gland.gland_model import Model

tester = Tester()
cythonizer = Cythonizer()
