"""
|whmod| is a base model for developing SVAT-like models.  "WHMod" stands for
"Wasserhaushaltsmodell", which is the German term for "water balance model".  In
contrast to most other :ref:`land models <land_models>` implemented in HydPy, the
primary purpose of its application models is not to calculate the runoff of river
basins but to calculate details of the water balance, like groundwater recharge, at
specific locations.
"""

# import..
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from hland
from hydpy.models.whmod.whmod_constants import *
from hydpy.models.whmod.whmod_model import Model
from hydpy.models.whmod.whmod_masks import Masks


tester = Tester()
cythonizer = Cythonizer()
