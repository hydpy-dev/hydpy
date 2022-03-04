# -*- coding: utf-8 -*-
"""This subpackage provides tools for cythonizing hydrological models as
well as the resulting Cython extension files (in subpackage `autogen`)."""

# import...
# from standard library
import os
import sys
import importlib

# from HydPy
from hydpy.cythons import autogen

autogenpath: str = autogen.__path__[0]
modulenames = sorted(
    str(fn.split(".")[0])
    for fn in os.listdir(autogenpath)
    if (fn.split(".")[-1] in ("pyd", "so") and not fn.startswith("c_"))
)

for modulename in modulenames:
    module = importlib.import_module(f"hydpy.cythons.autogen.{modulename}")
    sys.modules[f"hydpy.cythons.{modulename}"] = module
    locals()[modulename] = module
