
import sys
import importlib

_modulenames = ('pointerutils',
                'annutils',
                'configutils',
                'smoothutils')

for modulename in _modulenames:
    module = importlib.import_module('hydpy.cythons.autogen.'+modulename)
    sys.modules['hydpy.cythons.'+modulename] = module
