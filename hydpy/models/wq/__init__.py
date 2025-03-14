"""
The |wq.DOCNAME.long| base model provides features to implement small function-like
submodels for calculating discharge based on information like the current water level.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from exch
from hydpy.models.wq.wq_model import Model

tester = Tester()
cythonizer = Cythonizer()
