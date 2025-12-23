"""
The |rconc.DOCNAME.long| model family supplies features for calculating runoff
concentration.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.models.rconc.rconc_model import Model

tester = Tester()
cythonizer = Cythonizer()
