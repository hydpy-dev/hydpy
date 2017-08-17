
# import from...
# ...the standard library
import sys as __sys
# from HydPy
from hydpy.core import objecttools
from hydpy.core import indextools

projectname = None

options = objecttools.Options()
indexer = indextools.Indexer()
networkmanager = None
controlmanager = None
conditionmanager = None
sequencemanager = None
timegrids = None

pyversion = int(__sys.version[0])
_printprogress_indentation = -4
