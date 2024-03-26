"""Copy `hydpydoctestcustomize.pth` and `hydpydoctestcustomize.py` into the
site-packages folder to ensure the coverage measurement is complete when executing
tests in sub-processes."""

import os

import coverage

basepath = os.path.abspath(os.path.split(coverage.__path__[0])[0])
path_rcfile = os.path.join(basepath, "hydpy", "tests", ".coveragerc")
os.environ["COVERAGE_PROCESS_START"] = path_rcfile
os.environ["COVERAGE_RCFILE"] = path_rcfile
basepath_datafile = os.path.join(basepath, ".coverage")
os.environ["COVERAGE_FILE"] = basepath_datafile
coverage.process_startup()
