# -*- coding: utf-8 -*-
"""
The |ga.DOCNAME.long| base model provides features to implement infiltration methods
based on Green & Ampt-like wetting fronts.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from exch
from hydpy.models.ga.ga_model import Model

tester = Tester()
cythonizer = Cythonizer()
