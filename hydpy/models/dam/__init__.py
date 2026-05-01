"""
The |dam.DOCNAME.long| base model provides features to implement water barriers like
dams, weirs, lakes, or polders.
"""

from hydpy.auxs.anntools import ANN
from hydpy.auxs.ppolytools import Poly, PPoly
from hydpy.exe.modelimports import *
from hydpy.models.dam.dam_model import Model

tester = Tester()
cythonizer = Cythonizer()
