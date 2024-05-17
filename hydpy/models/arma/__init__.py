# -*- coding: utf-8 -*-
"""The HydPy-ARMA base model provides features to implement flood routing models based
on autoregressive (AR) and moving-average (MA) methods."""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from arma
from hydpy.models.arma.arma_model import Model

tester = Tester()
cythonizer = Cythonizer()
