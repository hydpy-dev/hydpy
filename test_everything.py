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

#tests = [fn.split('.')[0] for fn in os.listdir('.') if 
#         (fn.startswith('test') and fn.endswith('.py'))]
tests = {'test_01_pointer': None}
for name in tests.keys():
    module = importlib.import_module('hydpy.unittests.'+name)
    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    suite = unittest.TestLoader().loadTestsFromModule(module)
    tests[name] = runner.run(suite)

tests = {name: runner for name, runner in tests.items() if runner.failures}
if tests:
    print()
    print('At least one unit test failed in each of the following modules:')
    for name in sorted(tests.keys()):
        print('    %s (%d failures)' % (name, len(tests[name].failures))) 
    for name in sorted(tests.keys()):
        print()
        print('Detailed information on module %s:' % name)
        for idx, failure in enumerate(tests[name].failures):
            print('    Error no. %d:' % (idx+1))
            print('        %s' % failure[0])
            for line in failure[1].split('\n'):
                print('        %s' % line)
    sys.exit(1)
else:
    sys.exit(0)
        

    

