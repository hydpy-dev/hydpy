# -*- coding: utf-8 -*-
# pylint: disable=import-outside-toplevel
# due to importing hydpy after eventually changing its source path
"""Evaluate all doctests defined in the different modules and documentation files."""
from __future__ import annotations
import os
import sys
import importlib
import time
import unittest
import doctest
import warnings
from typing import Dict
from typing import Iterable, List, NamedTuple, Optional, NoReturn, Set, Sequence, Tuple

import click


def print_(*args: str) -> None:
    """Print immediately."""
    print(*args)
    sys.stdout.flush()


class _FilterFilenames:
    file_doctests: Set[str]

    def __init__(self, file_doctests: Iterable[str]) -> None:
        self.file_doctests = set(file_doctests)

    def __call__(self, filenames: Sequence[str]) -> Tuple[str, ...]:
        if self.file_doctests:
            return tuple(fn for fn in filenames if fn in self.file_doctests)
        return tuple(filenames)


DocTest = Dict[str, Tuple[unittest.TestResult, int]]


class DocTests(NamedTuple):
    """Stores the results of the successfull and failing test runs seperately."""

    successfull: DocTest
    failing: DocTest


@click.command()
@click.option(
    "-h",
    "--hydpy-path",
    type=str,
    required=False,
    default=None,
    help="Path of the HydPy package to be tested.",
)
@click.option(
    "-f",
    "--file-doctests",
    type=str,
    required=False,
    multiple=True,
    default=[],
    help="Name of the files that define the relevant doctests.",
)
@click.option(
    "-p",
    "--python-mode",
    type=bool,
    default=True,
    help="Execute all tests in Python-mode.",
)
@click.option(
    "-c",
    "--cython-mode",
    type=bool,
    default=True,
    help="Execute all tests in Cython-mode.",
)
def main(  # pylint: disable=too-many-branches
    hydpy_path: Optional[str],
    file_doctests: List[str],
    python_mode: bool,
    cython_mode: bool,
) -> NoReturn:
    """Perform all tests (first in Python mode, then in Cython mode)."""

    alldoctests: Dict[str, DocTests] = {}
    if python_mode:
        alldoctests["Python"] = DocTests(successfull={}, failing={})
    if cython_mode:
        alldoctests["Cython"] = DocTests(successfull={}, failing={})
    if not alldoctests:
        raise RuntimeError("Neither `Python` nor `Cython` mode selected for testing.")

    if hydpy_path is not None:
        sys.path.insert(0, hydpy_path)

    import hydpy
    from hydpy import config
    from hydpy import pub
    from hydpy.core import devicetools
    from hydpy.core import testtools

    filter_filenames = _FilterFilenames(file_doctests)
    pingtime: float = time.perf_counter()

    for mode, doctests in alldoctests.items():
        path_ = hydpy.__path__[0]
        filenames_: Sequence[str]
        for dirpath, _, filenames_ in os.walk(path_):
            if (  # pylint: disable=too-many-boolean-expressions
                ("__init__.py" not in filenames_)
                or dirpath.endswith("tests")
                or dirpath.endswith("docs")
                or dirpath.endswith("sphinx")
                or dirpath.endswith("autogen")
                or dirpath.endswith("build")
                or dirpath.endswith("__pycache__")
            ):
                continue
            filenames_ = filter_filenames(filenames_)
            packagename = dirpath.replace(os.sep, ".") + "."
            packagename = packagename[packagename.rfind("hydpy.") :]
            modulenames = [
                f"{packagename}{fn.split('.')[0]}"
                for fn in filenames_
                if fn.endswith(".py")
            ]
            docfilenames = [
                os.path.join(dirpath, fn)
                for fn in filenames_
                if fn[-4:] in (".rst", ".pyx")
            ]
            for name in modulenames + docfilenames:
                if time.perf_counter() > pingtime + 5 * 60:
                    print_("`run_doctests` still running...")
                    pingtime = time.perf_counter()
                if name.split(".")[-1] in ("apidoc", "prepare"):
                    continue
                if not name[-4:] in (".rst", ".pyx"):
                    module = importlib.import_module(name)
                suite = unittest.TestSuite()
                try:
                    if name[-4:] in (".rst", ".pyx"):
                        test = doctest.DocFileSuite(name, module_relative=False)
                    else:
                        test = doctest.DocTestSuite(module)
                    suite.addTest(test)
                except ValueError as exc:
                    if exc.args[-1] != "has no docstrings":
                        raise exc
                else:
                    del pub.projectname
                    del pub.timegrids
                    options = pub.options
                    del options.checkseries
                    options.ellipsis = 0
                    del pub.options.parameterstep
                    options.printprogress = False
                    options.reprdigits = 6
                    del pub.options.simulationstep
                    del options.timestampleft
                    del options.trimvariables
                    options.usecython = mode == "Cython"
                    del options.usedefaultvalues
                    del options.utclongitude
                    del options.utcoffset
                    del options.warnmissingcontrolfile
                    del options.warnmissingobsfile
                    del options.warnmissingsimfile
                    options.warnsimulationstep = False
                    options.warntrim = False
                    testtools.IntegrationTest.plotting_options = (
                        testtools.PlottingOptions()
                    )
                    if name[-4:] in (".rst", ".pyx"):
                        name = name[name.find("hydpy" + os.sep) :]
                    with warnings.catch_warnings(), open(
                        os.devnull, "w", encoding=config.ENCODING
                    ) as file_, devicetools.clear_registries_temporarily():
                        warnings.filterwarnings(action="error", module="hydpy")
                        warnings.filterwarnings(
                            action="ignore",
                            category=DeprecationWarning,
                            message="`np.bool`",
                        )
                        runner = unittest.TextTestRunner(stream=file_)
                        testresult = runner.run(suite)
                        nmbproblems = len(testresult.errors) + len(testresult.failures)
                        if nmbproblems:
                            doctests.failing[name] = (testresult, nmbproblems)
                        else:
                            doctests.successfull[name] = (testresult, nmbproblems)
                    problems = testresult.errors + testresult.failures
                    if problems:
                        pingtime = time.perf_counter()
                        print_(f"\nDetailed error information on module {name}:")
                        for idx, problem in enumerate(problems):
                            print_(f"    Error no. {idx+1}:")
                            print_(f"        {problem[0]}")
                            for line in problem[1].split("\n"):
                                print_(f"        {line}")

        if doctests.successfull:
            print_(f"\nIn the following modules, no doc test failed in {mode} mode:")
            for name, (testresult, _) in sorted(doctests.successfull.items()):
                if name[-4:] in (".rst", ".pyx"):
                    print_(f"    {name}")
                else:
                    print_(f"    {name} ({testresult.testsRun} successes)")
        if doctests.failing:
            print_(
                f"\nAt least one doc test failed in each of the following modules in "
                f"{mode} mode:"
            )
            for name, (testresult, nmbproblems) in sorted(doctests.failing.items()):
                print_(f"    {name} ({nmbproblems} failures/errors)")

    # Return the exit code.
    code = 0
    for mode, doctests in alldoctests.items():
        code = min(code + len(doctests.failing), 1)
        print_(
            f"\nrun_doctests.py found {len(doctests.failing)} failing doctest "
            f"suites in {mode} mode."
        )
    raise SystemExit(code)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
