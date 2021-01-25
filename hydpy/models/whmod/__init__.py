# -*- coding: utf-8 -*-

# import..
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from hland
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod.whmod_model import Model
from hydpy.models.whmod.whmod_masks import Masks


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
