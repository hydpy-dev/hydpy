"""
The G-Land model is the core of the HydPy implementation of the frequently applied
G models. Currently, the application models GR4, GR5 and GR6 are implemented.
For the modelling of snow processes within the G-Land processes the separate CEMA-Neige
snow module is implemented.
"""

# import..
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from gland
from hydpy.models.snow.snow_model import Model

tester = Tester()
cythonizer = Cythonizer()
