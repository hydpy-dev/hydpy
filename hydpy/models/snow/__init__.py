"""
The |snow.DOCNAME.complete| model family supplies methods for modelling snow processes.
"""

from hydpy.exe.modelimports import *

from hydpy.models.snow.snow_control import ZoneArea as _HRUArea
from hydpy.models.snow.snow_control import ZoneHeight  # ToDo: remove

ADDITIONAL_CONTROLPARAMETERS = (_HRUArea, ZoneHeight)  # ToDo: Turn into a model member?
del _HRUArea

from hydpy.models.snow.snow_masks import Masks  # pylint: disable=wrong-import-position
from hydpy.models.snow.snow_model import Model

tester = Tester()
cythonizer = Cythonizer()
