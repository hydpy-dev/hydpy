# -*- coding: utf-8 -*-
"""
The GrXJ-Land model is the core of the HydPy implementation of the
the frequently applied GRXJ models. The X stands for the model version, GR4J, GR5L, GR6J, respectively.
For the modelling of snow processes within the GRXJ-Land processes the CEMA-Neige snow module is implemented.
"""
# import..
# ...from HydPy
from hydpy.exe.modelimports import *
# ...from grxjland
from hydpy.models.grxjland.grxjland_model import Model

tester = Tester()
cythonizer = Cythonizer()
