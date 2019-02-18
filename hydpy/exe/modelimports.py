# -*- coding: utf-8 -*-
"""This module bundles imports generally required for implementing new models.

Module |modelimports| is supposed to shorten the import section
of base and application models implemented.  Just write:

>>> from hydpy.exe.modelimports import *

Thereafter, the following objects are available:
 * module |numpy|
 * numpys |numpy.nan| and |numpy.inf|
 * functions |parameterstep|, |simulationstep|, and |controlcheck|
   of module |importtools|
 * class |Tester| of module |testtools|
 * class |Cythonizer| of module |modelutils|

"""
# import...
# ...from site-packages
import numpy
from numpy import nan
from numpy import inf
# ...from HydPy
# Load the required `magic` functions into the local namespace.
from hydpy.core.importtools import parameterstep
from hydpy.core.importtools import simulationstep
from hydpy.core.importtools import controlcheck
from hydpy.core.autodoctools import autodoc_applicationmodel
from hydpy.core.testtools import Tester
from hydpy.cythons.modelutils import Cythonizer

__all__ = ['numpy',
           'nan',
           'inf',
           'parameterstep',
           'simulationstep',
           'controlcheck',
           'autodoc_applicationmodel',
           'Tester',
           'Cythonizer']
