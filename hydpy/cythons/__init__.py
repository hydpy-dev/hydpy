# -*- coding: utf-8 -*-

# import...
# from standard library
import os
import sys
import importlib
# from HydPy
from hydpy.cythons import autogen

modulenames = [
    str(fn.split('.')[0]) for fn in os.listdir(autogen.__path__[0])
    if (fn.endswith('.pyd') or fn.endswith('.so'))]

for modulename in modulenames:
    module = importlib.import_module(
        f'hydpy.cythons.autogen.{modulename}')
    sys.modules[f'hydpy.cythons.{modulename}'] = module
    locals()[modulename] = module
