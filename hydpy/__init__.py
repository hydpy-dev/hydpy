# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# due to using the HydPy class `OptionalImports` for importing site-packages
"""
HydPy

An interactive framework for the developement and a application of
hydrological models.
"""
# import...
# ...from standard library
import warnings
# ...from site-packages
warnings.filterwarnings('ignore')
import numpy
from numpy import nan
from scipy import integrate
# ...from HydPy
from hydpy.core import pubtools
pub = pubtools.Pub('pub')
from hydpy import config
from hydpy.core import dummytools
from hydpy.core import indextools
from hydpy.core import optiontools
from hydpy.cythons.autogen import configutils
from hydpy.core.auxfiletools import Auxfiler
from hydpy.core.devicetools import Element
from hydpy.core.devicetools import Elements
from hydpy.core.devicetools import Node
from hydpy.core.devicetools import Nodes
from hydpy.core.exceptiontools import HydPyDeprecationWarning
from hydpy.core.hydpytools import HydPy
from hydpy.core.importtools import prepare_model
from hydpy.core.importtools import reverse_model_wildcard_import
from hydpy.core.objecttools import classname
from hydpy.core.objecttools import print_values
from hydpy.core.objecttools import round_
from hydpy.core.objecttools import repr_
from hydpy.core.selectiontools import Selection
from hydpy.core.selectiontools import Selections
from hydpy.core.timetools import Date
from hydpy.core.timetools import Period
from hydpy.core.timetools import Timegrid
from hydpy.core.timetools import Timegrids
from hydpy.core.testtools import make_abc_testable
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
from hydpy.core.itemtools import AddItem
from hydpy.core.itemtools import GetItem
from hydpy.core.itemtools import SetItem
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
from hydpy.auxs.xmltools import XMLInterface
from hydpy.auxs.xmltools import run_simulation
from hydpy.exe.commandtools import exec_commands
from hydpy.exe.commandtools import execute_scriptfunction
from hydpy.exe.commandtools import run_subprocess
from hydpy.exe.commandtools import print_latest_logfile
from hydpy.exe.replacetools import xml_replace
from hydpy.exe.servertools import await_server
from hydpy.exe.servertools import start_server


pub.options = optiontools.Options()
pub.indexer = indextools.Indexer()
pub.config = configutils.Config()
dummies = dummytools.Dummies()

warnings.resetwarnings()
# Due to a Cython problem:
warnings.filterwarnings('ignore', category=ImportWarning)
warnings.filterwarnings('always', category=HydPyDeprecationWarning)
warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
warnings.filterwarnings('ignore', r'Using or importing the ABCs from')
warnings.filterwarnings('error', category=integrate.IntegrationWarning)

# Numpy introduced new string representations in version 1.14 affecting
# our doctests.  Hence, the old style is selected for now:
try:
    # pylint: disable=unexpected-keyword-arg
    numpy.set_printoptions(legacy='1.13')
except TypeError:   # pragma: no cover
    pass

pub.scriptfunctions['exec_commands'] = exec_commands
pub.scriptfunctions['run_simulation'] = run_simulation
pub.scriptfunctions['start_server'] = start_server
pub.scriptfunctions['await_server'] = await_server
pub.scriptfunctions['xml_replace'] = xml_replace

__all__ = ['config',
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
           'classname',
           'repr_',
           'round_',
           'Selection',
           'Selections',
           'Date',
           'Period',
           'Timegrid',
           'Timegrids',
           'make_abc_testable',
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
           'AddItem',
           'GetItem',
           'SetItem',
           'RiverBasinNumber',
           'RiverBasinNumbers',
           'RiverBasinNumbers2Selection',
           'dummies',
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
           'std_ratio',
           'XMLInterface',
           'run_simulation',
           'exec_commands',
           'execute_scriptfunction',
           'run_subprocess',
           'print_latest_logfile',
           'xml_replace',
           'await_server',
           'start_server']


if config.USEAUTODOC:
    import os
    import importlib
    from hydpy import auxs
    from hydpy import core
    from hydpy import cythons
    from hydpy import exe
    from hydpy import models
    from hydpy.core import autodoctools
    substituter = autodoctools.prepare_mainsubstituter()
    for subpackage in (auxs, core, cythons, exe):
        for filename in os.listdir(subpackage.__path__[0]):
            if filename.endswith('.py') and not filename.startswith('_'):
                module = importlib.import_module(
                    f'{subpackage.__name__}.{filename[:-3]}')
                autodoctools.autodoc_module(module)
    with pub.options.autocompile(False):
        for filename in os.listdir(models.__path__[0]):
            path = os.path.join(models.__path__[0], filename)
            if os.path.isdir(path) and not filename.startswith('_'):
                module = importlib.import_module(
                    f'{models.__name__}.{filename}')
                autodoctools.autodoc_basemodel(module)
        for filename in os.listdir(models.__path__[0]):
            if filename.endswith('.py') and not filename.startswith('_'):
                module = importlib.import_module(
                    f'{models.__name__}.{filename[:-3]}')
                autodoctools.autodoc_applicationmodel(module)
