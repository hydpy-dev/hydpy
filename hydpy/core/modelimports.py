"""This module bundles imports generally required for implementing nmodels.

Module :mod:`modelimports` is supposed to shorten the import section
of base and application models implemented.  Just write:

>>> from hydpy.core.modelimports import *

Thereafter, the following objects are available:
 * module :mod:`numpy`
 * numpys :obj:`~numpy.nan` and :obj:`~numpy.inf`
 * functions :func:`~hydpy.core.magictools.parameterstep`,
   :func:`~hydpy.core.magictools.simulationstep`,
   :func:`~hydpy.core.autodoctools.autodoc_basemodel`,
   of module :mod:`~hydpy.core.magictools`
 * class :class:`~hydpy.core.magictools.Tester`
   of module :mod:`~hydpy.core.magictools`
 * class :class:`~hydpy.cythons.modelutils.Cythonizer`
   of module :mod:`~hydpy.cythons.modelutils`

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
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.autodoctools import autodoc_basemodel
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer

