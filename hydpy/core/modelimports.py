# -*- coding: utf-8 -*-
"""This module bundles imports generally required for implementing new models.

Module |modelimports| is supposed to shorten the import section
of base and application models implemented.  Just write:

>>> from hydpy.core.modelimports import *

Thereafter, the following objects are available:
 * module |numpy|
 * numpys |numpy.nan| and |numpy.inf|
 * functions |parameterstep|, |simulationstep|, and |controlcheck|
   of module |importtools|
 * class |Tester| of module |testtools|
 * class |Cythonizer| of module |modelutils|

"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...third party
import numpy
from numpy import nan
from numpy import inf
# ...HydPy specific
# Load the required `magic` functions into the local namespace.
from hydpy.core.importtools import parameterstep
from hydpy.core.importtools import simulationstep
from hydpy.core.importtools import controlcheck
from hydpy.core.autodoctools import autodoc_basemodel
from hydpy.core.autodoctools import autodoc_applicationmodel
from hydpy.core.testtools import Tester
from hydpy.cythons.modelutils import Cythonizer

__all__ = ['division',
           'print_function',
           'numpy',
           'nan',
           'inf',
           'parameterstep',
           'simulationstep',
           'controlcheck',
           'autodoc_basemodel',
           'autodoc_applicationmodel',
           'Tester',
           'Cythonizer']
