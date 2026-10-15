"""Module |config| allows the user to configure `HydPy`.

The available options should not be changed during runtime.
"""

import os
from typing import Final

import numpy

USEAUTODOC = os.environ.get("HYDPY_USEAUTODOC") == "1"
"""A flag that indicates whether *HydPy's* automatic documentation manipulation 
features should be applied or not.  ctivate them before using  `Sphinx` to generate the 
online documentation.  However, one should not activate them  for regular applications, 
as this increases *HydPy's* initialisation time.  To  activate them, set the 
environment variable `HYDPY_USEAUTODOC` to "1" before importing hydpy."""

FASTCYTHON = True
"""A flag that indicates whether cythonizing should result in faster but more fragile 
models or slower but more robust models.  Setting this flag to False can be helpful 
when the implementation of new models or other Cython-related features introduces 
errors that do not result in informative error messages."""

PROFILECYTHON = False
"""A flag that indicates whether cythonized models should be fully accessible during 
profiling.  Setting this flag to True decreases performance and should be done by model 
or framework developers only."""

ENCODING = "utf-8"
"""Default encoding for all usages of |open|.  If you prefer to use your (different) 
locale encoding, define it explicitly or assign "locale"""

NP_FLOAT: Final = numpy.float64
"""Type of floating point values in NumPy arrays."""

NP_INT: Final = numpy.int64
"""Type of integer values in NumPy arrays."""

NP_BOOL: Final = numpy.bool_
"""Type of boolean values in NumPy arrays."""

TYPES_PY2NP: Final = {float: NP_FLOAT, int: NP_INT, bool: NP_BOOL}
"""Mapping from the required Python number types to the required NumPy number types."""
