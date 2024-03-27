# -*- coding: utf-8 -*-
"""HydPy-SW1D provides features for implementing models for approximating the
1-dimensional shallow water equations in a "hydrodynamic" manner to account for
situations like backwater effects that "hydrological" methods cannot handle well."""
# import...
# ...from HydPy
from hydpy.auxs.anntools import ANN
from hydpy.auxs.ppolytools import Poly, PPoly
from hydpy.exe.modelimports import *

# ...from sw1d
from hydpy.models.sw1d.sw1d_model import Model

tester = Tester()
cythonizer = Cythonizer()
