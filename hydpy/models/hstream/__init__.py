# -*- coding: utf-8 -*-
"""The HydPy-H-Stream model is an very simple routing approach.  More
precisely, it is a simplification of the Muskingum approach, which
itself can be seen as a naive finite difference solution of the
routing problem.
"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy.core.modelimports import *
# ...from hstream
from hydpy.models.hstream.hstream_parameters import Parameters
from hydpy.models.hstream.hstream_control import ControlParameters
from hydpy.models.hstream.hstream_derived import DerivedParameters
from hydpy.models.hstream.hstream_states import StateSequences
from hydpy.models.hstream.hstream_inlets import InletSequences
from hydpy.models.hstream.hstream_outlets import OutletSequences
from hydpy.models.hstream.hstream_model import Model

autodoc_basemodel()
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
