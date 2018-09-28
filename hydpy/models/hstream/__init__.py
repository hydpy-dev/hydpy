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
from hydpy.models.hstream.hstream_control import ControlParameters
from hydpy.models.hstream.hstream_derived import DerivedParameters
from hydpy.models.hstream.hstream_states import StateSequences
from hydpy.models.hstream.hstream_inlets import InletSequences
from hydpy.models.hstream.hstream_outlets import OutletSequences
from hydpy.models.hstream.hstream_masks import Masks
from hydpy.models.hstream.hstream_model import Model

autodoc_basemodel()

# pylint: disable=invalid-name
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
