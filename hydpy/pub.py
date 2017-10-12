
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
