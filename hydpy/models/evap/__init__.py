# -*- coding: utf-8 -*-
"""The |evap.DOCNAME.complete| model family supplies methods for calculating potential
evapotranspiration.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.evap.evap_masks import Masks
from hydpy.models.evap.evap_model import Model

tester = Tester()
cythonizer = Cythonizer()
