
# import from...
# ...the standard library
import sys as __sys
# ...from HydPy
from hydpy.core import objecttools as __objecttools
from hydpy.core import indextools as __indextools
from hydpy.cythons import configutils as __configutils

projectname = None

options = __objecttools.Options()
indexer = __indextools.Indexer()
networkmanager = None
controlmanager = None
conditionmanager = None
sequencemanager = None
timegrids = None

pyversion = int(__sys.version[0])
_printprogress_indentation = -4

config = __configutils.Config()

_am_i_an_exe = False
"""This parameter is set `True` within HydPy executables only.
Then different features that do not make much sense within an
executable (e.g. the cythonization of models) are disabled.
"""
