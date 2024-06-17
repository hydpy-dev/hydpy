# -*- coding: utf-8 -*-
"""
The |dam.DOCNAME.long| base model provides features to implement water barriers like
dams, weirs, lakes, or polders.
"""
# import...
# ...from HydPy
from hydpy.auxs.anntools import ANN
from hydpy.auxs.ppolytools import Poly, PPoly
from hydpy.exe.modelimports import *

# ...from dam
from hydpy.models.dam.dam_model import Model

tester = Tester()
cythonizer = Cythonizer()
