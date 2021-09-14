# -*- coding: utf-8 -*-
"""
The `HydPy-Exch` base model provides features to implement helper models that enable
other models to exchange data more freely.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from exch
from hydpy.models.exch.exch_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
