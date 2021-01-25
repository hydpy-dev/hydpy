# -*- coding: utf-8 -*-
"""The HydPy-H-Stream model is an very simple routing approach.  More
precisely, it is a simplification of the Muskingum approach, which
itself can be seen as a very simple finite difference solution of the
routing problem.
"""
# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from hstream
from hydpy.models.hstream.hstream_masks import Masks
from hydpy.models.hstream.hstream_model import Model

tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
