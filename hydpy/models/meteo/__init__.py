"""
The |meteo.DOCNAME.long| family supplies methods for calculating different
meteorological factors as input to other (hydrological) models.
"""

from hydpy.exe.modelimports import *
from hydpy.models.meteo.meteo_model import Model

tester = Tester()
cythonizer = Cythonizer()
