# -*- coding: utf-8 -*-
# pylint: disable=wildcard-import
"""
The HydPy-D base model provides features to implement water barriers like
dams, weirs, lakes, or polders.
"""
# import...
# ...from HydPy
from hydpy.auxs.anntools import ann
from hydpy.exe.modelimports import *
# ...from dam
from hydpy.models.dam.dam_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
