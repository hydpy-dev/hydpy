# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# due to using the HydPy class `OptionalImports` for importing site-packages
"""
*HydPy*

An interactive framework for the developement and a application of
hydrological models.
"""
# import...
# ...from standard library
import importlib
import os
import pkgutil
import warnings
from typing import *
# ...from site-packages
import numpy
from numpy import nan
# ...from HydPy
from hydpy.core import pubtools
pub = pubtools.Pub('pub')
from hydpy import config
from hydpy import models
from hydpy.core import dummytools
from hydpy.core import indextools
from hydpy.core import objecttools
from hydpy.core import optiontools
from hydpy.core import sequencetools
from hydpy.cythons.autogen import configutils
from hydpy.core.auxfiletools import Auxfiler
from hydpy.core.devicetools import Element
from hydpy.core.devicetools import Elements
from hydpy.core.devicetools import FusedVariable
from hydpy.core.devicetools import Node
from hydpy.core.devicetools import Nodes
from hydpy.core.exceptiontools import AttributeNotReady
from hydpy.core.exceptiontools import attrready
from hydpy.core.exceptiontools import getattr_
from hydpy.core.exceptiontools import hasattr_
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
from hydpy.core.timetools import TOY
from hydpy.core.testtools import make_abc_testable
from hydpy.core.testtools import NumericalDifferentiator
from hydpy.core.testtools import IntegrationTest
from hydpy.core.testtools import Open
from hydpy.core.testtools import TestIO
from hydpy.core.testtools import UnitTest
from hydpy.core.testtools import update_integrationtests
from hydpy.core.variabletools import INT_NAN
from hydpy.core.variabletools import sort_variables
from hydpy.auxs.armatools import ARMA
from hydpy.auxs.armatools import MA
from hydpy.auxs.anntools import ANN
from hydpy.auxs.anntools import ann
from hydpy.auxs.anntools import SeasonalANN
from hydpy.auxs.calibtools import Add
from hydpy.auxs.calibtools import Adaptor
from hydpy.auxs.calibtools import CalibrationInterface
from hydpy.auxs.calibtools import FactorAdaptor
from hydpy.auxs.calibtools import Multiply
from hydpy.auxs.calibtools import Replace
from hydpy.auxs.calibtools import ReplaceIUH
from hydpy.auxs.calibtools import Rule
from hydpy.auxs.calibtools import SumAdaptor
from hydpy.auxs.calibtools import TargetFunction
from hydpy.auxs.iuhtools import LinearStorageCascade
from hydpy.auxs.iuhtools import TranslationDiffusionEquation
from hydpy.core.itemtools import AddItem
from hydpy.core.itemtools import GetItem
from hydpy.core.itemtools import SetItem
from hydpy.auxs.networktools import RiverBasinNumber
from hydpy.auxs.networktools import RiverBasinNumbers
from hydpy.auxs.networktools import RiverBasinNumbers2Selection
from hydpy.auxs.statstools import aggregate_series
from hydpy.auxs.statstools import bias_abs
from hydpy.auxs.statstools import bias_rel
from hydpy.auxs.statstools import calc_mean_time
from hydpy.auxs.statstools import calc_mean_time_deviation
from hydpy.auxs.statstools import corr
from hydpy.auxs.statstools import corr2
from hydpy.auxs.statstools import evaluationtable
from hydpy.auxs.statstools import filter_series
from hydpy.auxs.statstools import hsepd
from hydpy.auxs.statstools import hsepd_manual
from hydpy.auxs.statstools import hsepd_pdf
from hydpy.auxs.statstools import kge
from hydpy.auxs.statstools import nse
from hydpy.auxs.statstools import nse_log
from hydpy.auxs.statstools import prepare_arrays
from hydpy.auxs.statstools import rmse
from hydpy.auxs.statstools import std_ratio
from hydpy.auxs.xmltools import XMLInterface
from hydpy.auxs.xmltools import run_simulation
from hydpy.exe.commandtools import exec_commands
from hydpy.exe.commandtools import exec_script
from hydpy.exe.commandtools import execute_scriptfunction
from hydpy.exe.commandtools import run_subprocess
from hydpy.exe.commandtools import start_shell
from hydpy.exe.commandtools import print_latest_logfile
from hydpy.exe.commandtools import test_everything
from hydpy.exe.replacetools import xml_replace
from hydpy.exe.servertools import await_server
from hydpy.exe.servertools import start_server


pub.options = optiontools.Options()
pub.indexer = indextools.Indexer()
pub.config = configutils.Config()
dummies = dummytools.Dummies()

warnings.filterwarnings('ignore', r'tostring')
# Numpy introduced new string representations in version 1.14 affecting
# our doctests.  Hence, the old style is selected for now:
try:
    # pylint: disable=unexpected-keyword-arg
    numpy.set_printoptions(legacy='1.13')
except TypeError:   # pragma: no cover
    pass

pub.scriptfunctions['await_server'] = await_server
pub.scriptfunctions['exec_commands'] = exec_commands
pub.scriptfunctions['exec_script'] = exec_script
pub.scriptfunctions['run_simulation'] = run_simulation
pub.scriptfunctions['start_shell'] = start_shell
pub.scriptfunctions['start_server'] = start_server
pub.scriptfunctions['test_everything'] = test_everything
pub.scriptfunctions['xml_replace'] = xml_replace

__all__ = ['aggregate_series',
           'config',
           'pub',
           'Auxfiler',
           'Element',
           'Elements',
           'FusedVariable',
           'Node',
           'Nodes',
           'AttributeNotReady',
           'attrready',
           'getattr_',
           'hasattr_',
           'HydPyDeprecationWarning',
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
           'TOY',
           'make_abc_testable',
           'NumericalDifferentiator',
           'IntegrationTest',
           'Open',
           'TestIO',
           'INT_NAN',
           'sort_variables',
           'UnitTest',
           'update_integrationtests',
           'ARMA',
           'MA',
           'ANN',
           'ann',
           'SeasonalANN',
           'Adaptor',
           'Add',
           'CalibrationInterface',
           'FactorAdaptor',
           'Multiply',
           'Replace',
           'ReplaceIUH',
           'Rule',
           'SumAdaptor',
           'TargetFunction',
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
           'corr2',
           'evaluationtable',
           'filter_series',
           'hsepd',
           'hsepd_manual',
           'hsepd_pdf',
           'kge',
           'nse',
           'nse_log',
           'prepare_arrays',
           'rmse',
           'std_ratio',
           'XMLInterface',
           'run_simulation',
           'exec_commands',
           'test_everything',
           'exec_script',
           'execute_scriptfunction',
           'start_shell',
           'run_subprocess',
           'print_latest_logfile',
           'xml_replace',
           'await_server',
           'start_server']

sequence2alias: Dict[sequencetools.TypesInOutSequence, str] = {}

_select = (
    sequencetools.InputSequence,
    sequencetools.FluxSequence,
    sequencetools.StateSequence,
)
for moduleinfo in pkgutil.walk_packages(models.__path__):
    if moduleinfo.ispkg:
        for group in ('inputs', 'fluxes', 'states'):
            modulepath = \
                f'hydpy.models.{moduleinfo.name}.{moduleinfo.name}_{group}'
            try:
                module = importlib.import_module(modulepath)
            except ModuleNotFoundError:
                continue
            for member in vars(module).values():
                if ((getattr(member, '__module__', None) == modulepath)
                        and issubclass(member, _select) and
                        member.NDIM == 0):
                    alias = f'{moduleinfo.name}_{member.__name__}'
                    sequence2alias[member] = alias
                    locals()[alias] = member
                    __all__.append(alias)

# noinspection PyUnresolvedReferences
if config.USEAUTODOC:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            action='ignore',
            category=FutureWarning,
        )
        from hydpy import auxs
        from hydpy import core
        from hydpy import cythons
        from hydpy import exe
        from hydpy.core import autodoctools
        substituter = autodoctools.prepare_mainsubstituter()
        for subpackage in (auxs, core, cythons, exe):
            for filename in os.listdir(subpackage.__path__[0]):
                if filename.endswith('.py') and not filename.startswith('_'):
                    module = importlib.import_module(
                        f'{subpackage.__name__}.{filename[:-3]}')
                    autodoctools.autodoc_module(module)
        autodoctools.autodoc_module(importlib.import_module('hydpy.examples'))
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
