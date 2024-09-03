# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# due to using the HydPy class `OptionalImports` for importing site-packages
"""
*HydPy*

An interactive framework for the developement and a application of hydrological models.
"""
# import...
# ...from standard library
from __future__ import annotations
import importlib
import os
import warnings
from typing import TYPE_CHECKING

# ...from site-packages
import numpy
from numpy import nan

# ...from HydPy
from hydpy.core import pubtools

pub = pubtools.Pub("pub")

from hydpy import config
from hydpy import models
from hydpy.core import indextools, objecttools, optiontools, sequencetools

if TYPE_CHECKING:
    from hydpy.cythons import configutils
else:
    from hydpy.cythons.autogen import configutils
from hydpy.core.auxfiletools import Auxfiler
from hydpy.core.devicetools import Element, Elements, FusedVariable, Node, Nodes
from hydpy.core.exceptiontools import AttributeNotReady, attrready, getattr_, hasattr_
from hydpy.core.exceptiontools import HydPyDeprecationWarning
from hydpy.core.hydpytools import HydPy
from hydpy.core.importtools import prepare_model, reverse_model_wildcard_import
from hydpy.core.itemtools import AddItem, GetItem, MultiplyItem, SetItem
from hydpy.core.netcdftools import summarise_ncfile
from hydpy.core.objecttools import classname, print_matrix, print_vector, round_, repr_
from hydpy.core.parametertools import KeywordArguments
from hydpy.core.selectiontools import Selection, Selections
from hydpy.core.seriestools import aggregate_series
from hydpy.core.timetools import Date, Period, Timegrid, Timegrids, TOY
from hydpy.core.testtools import (
    make_abc_testable,
    NumericalDifferentiator,
    IntegrationTest,
    Open,
    TestIO,
    UnitTest,
    update_integrationtests,
)
from hydpy.core.variabletools import INT_NAN, sort_variables
from hydpy.auxs.armatools import ARMA, MA
from hydpy.auxs.anntools import ANN
from hydpy.auxs.calibtools import (
    Add,
    Adaptor,
    CalibrationInterface,
    CalibSpec,
    CalibSpecs,
    FactorAdaptor,
    make_rules,
    Multiply,
    MultiplyIUH,
    Replace,
    ReplaceIUH,
    Rule,
    SumAdaptor,
    TargetFunction,
)
from hydpy.auxs.interptools import SeasonalInterpolator
from hydpy.auxs.iuhtools import LinearStorageCascade, TranslationDiffusionEquation
from hydpy.auxs.networktools import (
    RiverBasinNumber,
    RiverBasinNumbers,
    RiverBasinNumbers2Selection,
)
from hydpy.auxs.ppolytools import Poly, PPoly
from hydpy.auxs.statstools import (
    bias_abs,
    bias_rel,
    calc_mean_time,
    calc_mean_time_deviation,
    calc_weights,
    corr,
    corr2,
    filter_series,
    print_evaluationtable,
    hsepd,
    hsepd_manual,
    hsepd_pdf,
    kge,
    nse,
    nse_log,
    prepare_arrays,
    rmse,
    std_ratio,
    SummaryRowSimple,
    SummaryRowWeighted,
    var_ratio,
)
from hydpy.auxs.xmltools import XMLInterface, run_simulation
from hydpy.exe.commandtools import (
    exec_commands,
    exec_script,
    execute_scriptfunction,
    run_doctests,
    run_subprocess,
    start_shell,
    print_latest_logfile,
)
from hydpy.exe.replacetools import xml_replace
from hydpy.exe.servertools import await_server, start_server


__version__ = "6.1a0"

pub.options = optiontools.Options()
pub.indexer = indextools.Indexer()
pub.config = configutils.Config()

pub.scriptfunctions["await_server"] = await_server
pub.scriptfunctions["exec_commands"] = exec_commands
pub.scriptfunctions["exec_script"] = exec_script
pub.scriptfunctions["run_doctests"] = run_doctests
pub.scriptfunctions["run_simulation"] = run_simulation
pub.scriptfunctions["start_shell"] = start_shell
pub.scriptfunctions["start_server"] = start_server
pub.scriptfunctions["xml_replace"] = xml_replace

__all__ = [
    "config",
    "pub",
    "Auxfiler",
    "Element",
    "Elements",
    "FusedVariable",
    "Node",
    "Nodes",
    "AttributeNotReady",
    "attrready",
    "getattr_",
    "hasattr_",
    "HydPyDeprecationWarning",
    "HydPy",
    "prepare_model",
    "reverse_model_wildcard_import",
    "AddItem",
    "GetItem",
    "MultiplyItem",
    "SetItem",
    "summarise_ncfile",
    "classname",
    "print_matrix",
    "print_vector",
    "repr_",
    "round_",
    "KeywordArguments",
    "Selection",
    "Selections",
    "aggregate_series",
    "Date",
    "Period",
    "Timegrid",
    "Timegrids",
    "TOY",
    "make_abc_testable",
    "NumericalDifferentiator",
    "IntegrationTest",
    "Open",
    "TestIO",
    "INT_NAN",
    "sort_variables",
    "UnitTest",
    "update_integrationtests",
    "ARMA",
    "MA",
    "ANN",
    "Adaptor",
    "Add",
    "CalibrationInterface",
    "CalibSpec",
    "CalibSpecs",
    "FactorAdaptor",
    "make_rules",
    "Multiply",
    "MultiplyIUH",
    "Replace",
    "ReplaceIUH",
    "Rule",
    "SumAdaptor",
    "TargetFunction",
    "SeasonalInterpolator",
    "LinearStorageCascade",
    "TranslationDiffusionEquation",
    "RiverBasinNumber",
    "RiverBasinNumbers",
    "RiverBasinNumbers2Selection",
    "Poly",
    "PPoly",
    "nan",
    "bias_abs",
    "bias_rel",
    "calc_mean_time",
    "calc_mean_time_deviation",
    "calc_weights",
    "corr",
    "corr2",
    "filter_series",
    "print_evaluationtable",
    "hsepd",
    "hsepd_manual",
    "hsepd_pdf",
    "kge",
    "nse",
    "nse_log",
    "prepare_arrays",
    "rmse",
    "std_ratio",
    "SummaryRowSimple",
    "SummaryRowWeighted",
    "var_ratio",
    "XMLInterface",
    "run_simulation",
    "exec_commands",
    "exec_script",
    "execute_scriptfunction",
    "start_shell",
    "run_doctests",
    "run_subprocess",
    "print_latest_logfile",
    "xml_replace",
    "await_server",
    "start_server",
]

sequence2alias: dict[sequencetools.InOutSequenceTypes, str] = {}

if config.USEAUTODOC:
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", category=FutureWarning)
        from hydpy import auxs
        from hydpy import core
        from hydpy import cythons
        from hydpy import exe
        from hydpy import interfaces
        from hydpy.core import autodoctools

        substituter = autodoctools.prepare_mainsubstituter()
        for subpackage in (auxs, core, cythons, interfaces, exe):
            subpackagepath = subpackage.__path__[0]
            for filename in sorted(os.listdir(subpackagepath)):
                if filename.endswith(".py") and not filename.startswith("_"):
                    module = importlib.import_module(
                        f"{subpackage.__name__}.{filename[:-3]}"
                    )
                    autodoctools.autodoc_module(module)
        modelpath: str = models.__path__[0]
        for filename in sorted(os.listdir(modelpath)):
            path = os.path.join(modelpath, filename)
            if os.path.isdir(path) and not filename.startswith("_"):
                module = importlib.import_module(f"{models.__name__}.{filename}")
                autodoctools.autodoc_basemodel(module)
        for filename in sorted(os.listdir(modelpath)):
            if filename.endswith(".py") and not filename.startswith("_"):
                module = importlib.import_module(f"{models.__name__}.{filename[:-3]}")
                autodoctools.autodoc_applicationmodel(module)
