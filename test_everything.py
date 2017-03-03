# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:57:25 2017

@author: tyralla
"""


from __future__ import division, print_function
import os
import sys
import importlib
import unittest
import doctest

if 'test_as_site-package' in sys.argv:
    paths = [path for path in sys.path if path.endswith('-packages')]
    for path in paths:
        sys.path.insert(0, path)

import hydpy.unittests
filenames = os.listdir(hydpy.unittests.__path__[0])
unittests = {fn.split('.')[0]: None for fn in filenames if
             (fn.startswith('test') and fn.endswith('.py'))}
for name in unittests.keys():
    module = importlib.import_module('hydpy.unittests.'+name)
    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
    suite = unittest.TestLoader().loadTestsFromModule(module)
    unittests[name] = runner.run(suite)

successfulunittests = {name: runner for name, runner in unittests.items()
                       if not runner.failures}
failedunittests = {name: runner for name, runner in unittests.items()
                   if runner.failures}

if successfulunittests:
    print()
    print('In the following modules, no unit test failed:')
    for name in sorted(successfulunittests.keys()):
        print('    %s (%d successes)'
              % (name, successfulunittests[name].testsRun))
if failedunittests:
    print()
    print('At least one unit test failed in each of the following modules:')
    for name in sorted(failedunittests.keys()):
        print('    %s (%d failures)'
              % (name, len(failedunittests[name].failures)))
    for name in sorted(failedunittests.keys()):
        print()
        print('Detailed information on module %s:' % name)
        for idx, failure in enumerate(failedunittests[name].failures):
            print('    Error no. %d:' % (idx+1))
            print('        %s' % failure[0])
            for line in failure[1].split('\n'):
                print('        %s' % line)

from hydpy import pub
pub.options.reprcomments = False
import hydpy
from hydpy.framework import devicetools
alldoctests = ({}, {})
allsuccessfuldoctests = ({}, {})
allfaileddoctests = ({}, {})
iterable = zip(('Python', 'Cython'), alldoctests,
               allsuccessfuldoctests, allfaileddoctests)
for (mode, doctests, successfuldoctests, faileddoctests) in iterable:
    pub.options.usecython = mode=='Cython'
    for dirinfo in os.walk(hydpy.__path__[0]):
        if dirinfo[0].endswith('unittests') or not '__init__.py' in dirinfo[2]:
            continue
        packagename = dirinfo[0].replace(os.sep, '.')+'.'
        packagename = packagename[packagename.find('hydpy.'):]
        level = packagename.count('.')-1
        modulenames = [packagename+fn.split('.')[0]
                       for fn in dirinfo[2] if fn.endswith('.py')]
        for modulename in modulenames:
            module = importlib.import_module(modulename)
            runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))
            suite = unittest.TestSuite()
            try:
                suite.addTest(doctest.DocTestSuite(module))
            except ValueError:
                pass
            else:
                pub.timegrids = None
                pub.options.reprcomments = False
                devicetools.Node.clearregistry()
                devicetools.Element.clearregistry()
                doctests[modulename] = runner.run(suite)

    successfuldoctests.update({name: runner for (name, runner)
                              in doctests.items() if not runner.failures})
    faileddoctests.update({name: runner for (name, runner )
                          in doctests.items() if runner.failures})

    if successfuldoctests:
        print()
        print('In the following modules, no doc test failed in %s mode:'
              % mode)
        for name in sorted(successfuldoctests.keys()):
            print('    %s (%d successes)'
                  % (name, successfuldoctests[name].testsRun))
    if faileddoctests:
        print()
        print('At least one doc test failed in each of the following modules '
              'in %s mode:' % mode)
        for name in sorted(faileddoctests.keys()):
            print('    %s (%d failures)'
                  % (name, len(faileddoctests[name].failures)))
        for name in sorted(faileddoctests.keys()):
            print()
            print('Detailed information on module %s:' % name)
            for idx, failure in enumerate(faileddoctests[name].failures):
                print('    Error no. %d:' % (idx+1))
                print('        %s' % failure[0])
                for line in failure[1].split('\n'):
                    print('        %s' % line)

if failedunittests or allfaileddoctests[0] or allfaileddoctests[1]:
    sys.exit(1)
else:
    sys.exit(0)
