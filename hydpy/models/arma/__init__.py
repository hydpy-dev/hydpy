"""
|arma.DOCNAME.complete| provides features to implement flood routing models based on
autoregressive (AR) and moving-average (MA) methods.
"""

from hydpy.exe.modelimports import *
from hydpy.models.arma.arma_model import Model

tester = Tester()
cythonizer = Cythonizer()
