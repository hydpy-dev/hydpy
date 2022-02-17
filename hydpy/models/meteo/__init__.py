# -*- coding: utf-8 -*-
"""The HydPy-Meteo model family supplies methods for calculating different
meteorological factors serving as input to other (hydrological) models.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.meteo.meteo_model import Model

tester = Tester()
cythonizer = Cythonizer()
