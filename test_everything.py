# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:57:25 2017

@author: tyralla
"""


from __future__ import division, print_function
import unittest
import os
import importlib
import sys
for (idx, path) in enumerate(sys.path):
    if path.endswith('site-packages'):
        del(sys.path[idx])
        break
sys.path.insert(0, path)

#module_names = [fn.split('.')[0] for fn in os.listdir('.') if 
#                (fn.startswith('test') and fn.endswith('.py'))]
module_names = ['test_01_pointer']
for module_name in module_names:
    module = importlib.import_module('hydpy.unittests.'+module_name)
    suite = unittest.TestLoader().loadTestsFromModule(module)
    unittest.TextTestRunner(verbosity=0).run(suite)

