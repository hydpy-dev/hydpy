# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...third party
import numpy
from numpy import nan
# ...HydPy specific
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

from hydpy.models.llake.llake_parameters import Parameters
from hydpy.models.llake.llake_control import ControlParameters
from hydpy.models.llake.llake_sequences import Sequences
from hydpy.models.llake.llake_model import Model

tester = Tester()


