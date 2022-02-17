# -*- coding: utf-8 -*-
"""The HydPy-Evap model family supplies methods for calculating potential
evapotranspiration.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.evap.evap_model import Model

tester = Tester()
cythonizer = Cythonizer()
