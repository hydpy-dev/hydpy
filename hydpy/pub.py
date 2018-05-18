
# import from...
# ...the standard library
import sys as _sys

projectname = None

options = None
indexer = None
networkmanager = None
controlmanager = None
conditionmanager = None
sequencemanager = None
timegrids = None

pyversion = int(_sys.version[0])
_printprogress_indentation = -4

_is_hydpy_bundled = getattr(_sys, 'frozen', False)
"""This parameter is set `True` within HydPy executables only.
Then different features that do not make much sense within an
executable (e.g. the cythonization of models) are disabled.
"""
