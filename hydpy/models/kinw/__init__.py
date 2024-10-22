"""
.. _`LARSIM`: http://www.larsim.de/en/the-model/

The |kinw.DOCNAME.long| model family provides features for implementing storage based
routing methods similar to those implemented by the water balance model `LARSIM`_.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.auxs.anntools import ANN
from hydpy.auxs.ppolytools import Poly, PPoly

# ...from kinw
from hydpy.models.kinw.kinw_model import Model

tester = Tester()
cythonizer = Cythonizer()
