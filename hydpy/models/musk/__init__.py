"""|musk.DOCNAME.long| provides features for implementing Muskingum-like routing
methods, which are finite difference solutions of the routing problem."""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from musk
from hydpy.models.musk.musk_masks import Masks
from hydpy.models.musk.musk_model import Model

tester = Tester()
cythonizer = Cythonizer()
