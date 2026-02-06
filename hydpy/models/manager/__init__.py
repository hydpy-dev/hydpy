"""The |manager.DOCNAME.complete| base model provides features for implementing models
that coordinate other models."""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from dam
from hydpy.models.manager.manager_model import Model

tester = Tester()
cythonizer = Cythonizer()
