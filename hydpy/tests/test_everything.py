# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# due to importing hydpy after the site-packages have been priorised
# (see the comments below)
"""Test all "conventional" unit tests defined in subpackage `tests` and
all doctests defined in the different modules and documentation files.
"""

import os
import sys
import importlib
import time
import unittest
import doctest
import warnings
from typing import *


def print_(*args: str) -> None:
    """Print immediately."""
    print(*args)
    sys.stdout.flush()


class _FilterFilenames:
    def __init__(self, argv: List[str]) -> None:
        self.selection: List[str] = []
        for arg_ in argv:
            if arg_.startswith("select="):
                self.selection.extend(_ for _ in arg_[7:].split(","))

    def __call__(self, names: Sequence[str]) -> List[str]:
        if self.selection:
            return [_ for _ in names if _ in self.selection]
        return list(names)


filter_filenames = _FilterFilenames(sys.argv)
testpath = None
for arg in sys.argv:
    if arg.startswith("test_path="):
        testpath = arg.split("=")[-1]

forcecompiling = "forcecompiling=False" not in sys.argv

# Priorise site-packages (on Debian-based Linux distributions as Ubuntu
# also dist-packages) in the import order to make sure, the following
# imports refer to the newly build hydpy package on the respective computer.
if testpath is None:
    paths = [path for path in sys.path if path.endswith("-packages")]
    for path in paths:
        sys.path.insert(0, path)
else:
    sys.path.insert(0, testpath)

# Import all hydrological models to trigger the automatic cythonization
# mechanism of HydPy.
from hydpy import pub

with pub.options.forcecompiling(forcecompiling), pub.options.skipdoctests(True):
    import hydpy.models

    path_: str = hydpy.models.__path__[0]  # type: ignore[attr-defined, name-defined]
    for name in [fn.split(".")[0] for fn in sorted(os.listdir(path_))]:
        if name != "__init__":
            modulename = "hydpy.models." + name
            alreadyimported = modulename in sys.modules
            module = importlib.import_module(modulename)
            if alreadyimported:
                importlib.reload(module)


# Write the required configuration and alias files to be generated dynamically.
from hydpy.core.aliastools import write_sequencealiases
from hydpy.auxs.xmltools import XSDWriter

write_sequencealiases()
XSDWriter().write_xsd()

# Perform all tests (first in Python mode, then in Cython mode)
import hydpy
from hydpy.core import devicetools
from hydpy.core import testtools

pingtime: float = time.perf_counter()

DocTest = Dict[str, Tuple[unittest.TestResult, int]]
DocTests = Tuple[DocTest, DocTest]
alldoctests: DocTests = ({}, {})
allsuccessfuldoctests: DocTests = ({}, {})
allfaileddoctests: DocTests = ({}, {})
for (mode, doctests, successfuldoctests, faileddoctests) in zip(
    ("Python", "Cython"), alldoctests, allsuccessfuldoctests, allfaileddoctests
):
    path_ = hydpy.__path__[0]  # type: ignore[attr-defined, name-defined]
    for dirpath, dirnames, filenames_ in os.walk(path_):
        is_package = "__init__.py" in filenames_
        if "__init__.py" not in filenames_:
            continue
        if (
            dirpath.endswith("tests")
            or dirpath.endswith("docs")
            or dirpath.endswith("sphinx")
            or dirpath.endswith("autogen")
        ):
            continue
        if dirpath.endswith("build") or dirpath.endswith("__pycache__"):
            continue
        filenames_ = filter_filenames(filenames_)
        packagename = dirpath.replace(os.sep, ".") + "."
        packagename = packagename[packagename.rfind("hydpy.") :]
        level = packagename.count(".") - 1
        modulenames = [
            packagename + fn.split(".")[0] for fn in filenames_ if fn.endswith(".py")
        ]
        docfilenames = [
            os.path.join(dirpath, fn)
            for fn in filenames_
            if fn[-4:] in (".rst", ".pyx")
        ]
        for name in modulenames + docfilenames:
            if time.perf_counter() > pingtime + 5 * 60:
                print_("`test_everything` still running...")
                pingtime = time.perf_counter()
            if name.split(".")[-1] in ("apidoc", "prepare", "modify_html"):
                continue
            if not name[-4:] in (".rst", ".pyx"):
                module = importlib.import_module(name)
            suite = unittest.TestSuite()
            try:
                if name[-4:] in (".rst", ".pyx"):
                    suite.addTest(
                        doctest.DocFileSuite(
                            name,
                            module_relative=False,
                            optionflags=doctest.ELLIPSIS,
                        ),
                    )
                elif sys.version_info[:2] < (3, 7):
                    # numpy 1.20 fixed some error messages but does not support
                    # Python 3.6, which we still need for compatibility with arcpy
                    suite.addTest(
                        doctest.DocTestSuite(
                            module,
                            optionflags=doctest.IGNORE_EXCEPTION_DETAIL,
                        ),
                    )
                else:
                    suite.addTest(
                        doctest.DocTestSuite(
                            module,
                            optionflags=doctest.ELLIPSIS,
                        ),
                    )
            except ValueError as exc:
                if exc.args[-1] != "has no docstrings":
                    raise exc
            else:
                del pub.projectname
                del pub.timegrids
                opt = pub.options
                opt.usecython = mode == "Cython"
                opt.ellipsis = 0
                opt.flattennetcdf = False
                opt.isolatenetcdf = False
                del pub.options.parameterstep
                opt.printincolor = False
                opt.printprogress = False
                opt.reprcomments = False
                opt.reprdigits = 6
                del pub.options.simulationstep
                opt.timeaxisnetcdf = 1
                opt.usedefaultvalues = False
                opt.utclongitude = 15
                opt.utcoffset = 60
                opt.warnsimulationstep = False
                opt.warntrim = False
                testtools.IntegrationTest.plotting_options = testtools.PlottingOptions()
                if name[-4:] in (".rst", ".pyx"):
                    name = name[name.find("hydpy" + os.sep) :]
                with warnings.catch_warnings(), open(
                    os.devnull, "w"
                ) as file_, devicetools.clear_registries_temporarily():
                    warnings.filterwarnings(
                        action="error",
                        module="hydpy",
                    )
                    warnings.filterwarnings(
                        action="ignore",
                        category=DeprecationWarning,
                        message="`np.bool`",
                    )
                    runner = unittest.TextTestRunner(stream=file_)
                    testresult = runner.run(suite)
                    doctests[name] = (
                        testresult,
                        len(testresult.errors) + len(testresult.failures),
                    )
                problems = testresult.errors + testresult.failures
                if problems:
                    pingtime = time.perf_counter()
                    print_(f"\nDetailed error information on module {name}:")
                    for idx, problem in enumerate(problems):
                        print_(f"    Error no. {idx+1}:")
                        print_(f"        {problem[0]}")
                        for line in problem[1].split("\n"):
                            print_(f"        {line}")
    successfuldoctests.update(
        {
            name: (runner, nmbproblems)
            for name, (runner, nmbproblems) in doctests.items()
            if not nmbproblems
        }
    )
    faileddoctests.update(
        {
            name: (runner, nmbproblems)
            for name, (runner, nmbproblems) in doctests.items()
            if nmbproblems
        }
    )

    if successfuldoctests:
        print_(f"\nIn the following modules, no doc test failed in {mode} mode:")
        for name, (testresult, _) in sorted(successfuldoctests.items()):
            if name[-4:] in (".rst", ".pyx"):
                print_(f"    {name}")
            else:
                print_(f"    {name} ({testresult.testsRun} successes)")
    if faileddoctests:
        print_(
            f"\nAt least one doc test failed in each of the "
            f"following modules in {mode} mode:"
        )
        for name, (testresult, nmbproblems) in sorted(faileddoctests.items()):
            print_(f"    {name} ({nmbproblems} failures/errors)")

# Return the exit code.
print_(
    f"\ntest_everything.py found {len(allfaileddoctests[0])} failing "
    f"doctest suites in Python mode and {len(allfaileddoctests[1])} "
    f"failing doctest suites in Cython mode."
)
if allfaileddoctests[0] or allfaileddoctests[1]:
    sys.exit(1)
else:
    sys.exit(0)
