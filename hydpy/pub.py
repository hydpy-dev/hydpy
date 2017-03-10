
# import from...
# ...the standard library
import sys as __sys
# from HydPy
from hydpy.core import objecttools

projectname = None

options = objecttools.Options()

networkmanager = None
controlmanager = None
conditionmanager = None
sequencemanager = None
timegrids = None

pyversion = int(__sys.version[0])


