
import sys as __sys
import platform as __platform

from . import objecttools 

projectname = None

options = objecttools.Options()

networkmanager = None
controlmanager = None
conditionmanager = None
sequencemanager = None
timegrids = None


if __sys.platform.startswith('win'):
    system = 'windows'
else:
    system = 'linux'
# ...the bit version
if __platform.machine().endswith('64'):
    system += '_64bit'
else:
    system += '32bit'
