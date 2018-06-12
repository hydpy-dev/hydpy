"""
HydPy

An interactive framework for the developement and a application of
hydrological models.
"""
# import...
# ...from standard library
import sys
import warnings
try:
    import builtins
except ImportError:
    import __builtin__ as builtins
# ...from site-packages
from hydpy.core.exceptiontools import OptionalImport
import numpy
from numpy import nan
from scipy import integrate
pandas = OptionalImport(
    'pandas',
    ['import pandas'])
pyplot = OptionalImport(
    'matplotlib.pyplot',
    ['from matplotlib import pyplot'])
# ...from HydPy
from hydpy import pub
from hydpy.core import dummytools
from hydpy.core import indextools
from hydpy.core import optiontools
from hydpy.cythons import configutils
from hydpy.core.autodoctools import prepare_mainsubstituter
from hydpy.core.auxfiletools import Auxfiler
from hydpy.core.devicetools import Element
from hydpy.core.devicetools import Elements
from hydpy.core.devicetools import Node
from hydpy.core.devicetools import Nodes
from hydpy.core.hydpytools import HydPy
from hydpy.core.importtools import prepare_model
from hydpy.core.importtools import reverse_model_wildcard_import
from hydpy.core.objecttools import HydPyDeprecationWarning
from hydpy.core.objecttools import print_values
from hydpy.core.objecttools import round_
from hydpy.core.objecttools import repr_
from hydpy.core.selectiontools import Selection
from hydpy.core.selectiontools import Selections
from hydpy.core.timetools import Date
from hydpy.core.timetools import Period
from hydpy.core.timetools import Timegrid
from hydpy.core.timetools import Timegrids
from hydpy.core.testtools import IntegrationTest
from hydpy.core.testtools import Open
from hydpy.core.testtools import TestIO
from hydpy.core.testtools import UnitTest
from hydpy.auxs.armatools import ARMA
from hydpy.auxs.armatools import MA
from hydpy.auxs.anntools import ANN
from hydpy.auxs.anntools import ann
from hydpy.auxs.anntools import SeasonalANN
from hydpy.auxs.iuhtools import LinearStorageCascade
from hydpy.auxs.iuhtools import TranslationDiffusionEquation
from hydpy.auxs.networktools import RiverBasinNumber
from hydpy.auxs.networktools import RiverBasinNumbers
from hydpy.auxs.networktools import RiverBasinNumbers2Selection
from hydpy.auxs.statstools import bias_abs
from hydpy.auxs.statstools import bias_rel
from hydpy.auxs.statstools import calc_mean_time
from hydpy.auxs.statstools import calc_mean_time_deviation
from hydpy.auxs.statstools import corr
from hydpy.auxs.statstools import evaluationtable
from hydpy.auxs.statstools import hsepd
from hydpy.auxs.statstools import hsepd_manual
from hydpy.auxs.statstools import hsepd_pdf
from hydpy.auxs.statstools import nse
from hydpy.auxs.statstools import prepare_arrays
from hydpy.auxs.statstools import std_ratio


pub.options = optiontools.Options()
pub.indexer = indextools.Indexer()
pub.config = configutils.Config()
dummies = dummytools.Dummies()   # pylint: disable=invalid-name


def customwarn(message, category, filename, lineno, file=None, line=None):
    """Redirect warnings to `stdout`."""
    sys.stdout.write(warnings.formatwarning(
        message, category, filename, lineno))


warnings.showwarning = customwarn
warnings.filterwarnings('always', category=HydPyDeprecationWarning)
warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
warnings.filterwarnings('error', category=integrate.IntegrationWarning)

# Numpy introduced new string representations in version 1.14 affecting
# our doctests.  Hence, the old style is selected for now:
try:
    # pylint: disable=unexpected-keyword-arg
    numpy.set_printoptions(legacy='1.13')
except TypeError:
    pass

substituter = prepare_mainsubstituter()


__all__ = ['builtins',
           'pandas',
           'pyplot',
           'pub',
           'Auxfiler',
           'Element',
           'Elements',
           'Node',
           'Nodes',
           'HydPy',
           'prepare_model',
           'reverse_model_wildcard_import',
           'print_values',
           'repr_',
           'round_',
           'Selection',
           'Selections',
           'Date',
           'Period',
           'Timegrid',
           'Timegrids',
           'IntegrationTest',
           'Open',
           'TestIO',
           'UnitTest',
           'ARMA',
           'MA',
           'ANN',
           'ann',
           'SeasonalANN',
           'LinearStorageCascade',
           'TranslationDiffusionEquation',
           'RiverBasinNumber',
           'RiverBasinNumbers',
           'RiverBasinNumbers2Selection',
           'nan',
           'bias_abs',
           'bias_rel',
           'calc_mean_time',
           'calc_mean_time_deviation',
           'corr',
           'evaluationtable',
           'hsepd',
           'hsepd_manual',
           'hsepd_pdf',
           'nse',
           'prepare_arrays',
           'std_ratio']
