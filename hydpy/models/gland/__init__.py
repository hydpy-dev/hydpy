# -*- coding: utf-8 -*-
"""
|gland| is the core of the HydPy implementation of the frequently applied Génie
Rurale models, of which GR4J :cite:p:`ref-Perrin2007` is probably the most known one.
"""
# import..
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from gland
from hydpy.models.gland.gland_model import Model

tester = Tester()
cythonizer = Cythonizer()
