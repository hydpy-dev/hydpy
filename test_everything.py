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
if 'test_as_site-package' in sys.argv:
    for (idx, path) in enumerate(sys.path):
        if path.endswith('site-packages'):
            del(sys.path[idx])
            break
    sys.path.insert(0, path)
import hydpy.unittests

filenames = os.listdir(hydpy.unittests.__path__[0])
tests = {fn.split('.')[0]: None for fn in filenames if 
         (fn.startswith('test') and fn.endswith('.py'))}
for name in tests.keys():
    module = importlib.import_module('hydpy.unittests.'+name)
    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    suite = unittest.TestLoader().loadTestsFromModule(module)
    tests[name] = runner.run(suite)

successfultests = {name: runner for name, runner in tests.items() 
                   if not runner.failures}
failedtests = {name: runner for name, runner in tests.items() 
               if runner.failures}

if successfultests:
    print()
    print('In the following modules, no unit test failed:')
    for name in sorted(successfultests.keys()):
        print('    %s (%d successes)' % (name, successfultests[name].testsRun))    
if failedtests:
    print()
    print('At least one unit test failed in each of the following modules:')
    for name in sorted(failedtests.keys()):
        print('    %s (%d failures)' % (name, len(failedtests[name].failures))) 
    for name in sorted(failedtests.keys()):
        print()
        print('Detailed information on module %s:' % name)
        for idx, failure in enumerate(failedtests[name].failures):
            print('    Error no. %d:' % (idx+1))
            print('        %s' % failure[0])
            for line in failure[1].split('\n'):
                print('        %s' % line)
    sys.exit(1)
else:
    sys.exit(0)
        

    

